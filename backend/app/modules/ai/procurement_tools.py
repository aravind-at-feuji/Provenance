"""
app/modules/ai/procurement_tools.py — Phase 1 agent tools.

Tools registered here:
  - create_material_request   Create MR from NL description + items list
  - approve_document          Approve or reject a document via its workflow

These are called from the investigation agent when procurement intent is detected.
All writes go to real DB tables; no mock data is generated.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.approvals.service import ApprovalService, WorkflowNotFound, NotPendingStep
from app.modules.procurement.schemas import MaterialRequestCreate, MRLineItemCreate
from app.modules.procurement.service import ProcurementService, MRNotFound, InvalidStatusTransition

logger = structlog.get_logger(__name__)


class ProcurementToolError(Exception):
    pass


async def tool_create_material_request(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: str | None,
    title: str,
    items: list[dict[str, Any]],
    required_by: str | None = None,
    priority: str = "medium",
    department: str | None = None,
    justification: str | None = None,
    currency: str | None = None,
    auto_submit: bool = False,
) -> dict[str, Any]:
    """
    Create a Material Request (optionally submit for approval immediately).

    items: list of {description, quantity, unit_of_measure?, estimated_unit_price?, currency?}
    required_by: ISO date string (YYYY-MM-DD), optional
    auto_submit: if True, submit to approval workflow right after creation
    """
    from datetime import date

    required_by_date = None
    if required_by:
        try:
            required_by_date = date.fromisoformat(required_by)
        except ValueError:
            logger.warning("procurement_tool_invalid_date", required_by=required_by)

    line_items = [
        MRLineItemCreate(
            description=li.get("description", ""),
            quantity=float(li.get("quantity", 1)),
            unit_of_measure=li.get("unit_of_measure"),
            estimated_unit_price=li.get("estimated_unit_price"),
            currency=li.get("currency", currency),
            item_id=uuid.UUID(li["item_id"]) if li.get("item_id") else None,
            preferred_supplier_id=uuid.UUID(li["preferred_supplier_id"]) if li.get("preferred_supplier_id") else None,
        )
        for li in items
    ]

    svc = ProcurementService(db)
    data = MaterialRequestCreate(
        title=title,
        required_by_date=required_by_date,
        priority=priority,  # type: ignore[arg-type]
        department=department,
        justification=justification,
        currency=currency,
        line_items=line_items,
    )
    mr = await svc.create_mr(org_id, data, user_id=user_id)

    result: dict[str, Any] = {
        "action": "create_material_request",
        "mr_number": mr.mr_number,
        "mr_id": str(mr.id),
        "status": mr.status,
        "title": mr.title,
        "total_estimated_amount": float(mr.total_estimated_amount or 0),
        "currency": mr.currency,
        "line_item_count": len(mr.line_items or []),
    }

    if auto_submit:
        try:
            mr = await svc.submit_mr(mr.id, org_id, user_id=user_id)
            result["status"] = mr.status
            result["submitted"] = True
        except InvalidStatusTransition as exc:
            result["submit_error"] = str(exc)

    logger.info("procurement_tool_mr_created", mr_number=mr.mr_number, org_id=str(org_id))
    return result


async def tool_approve_document(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: str | None,
    document_type: str,
    document_id: str,
    action: str,
    comments: str | None = None,
) -> dict[str, Any]:
    """
    Approve or reject a document by finding its active approval workflow.

    document_type: material_request | purchase_order | invoice
    document_id: UUID string
    action: approve | reject
    """
    if action not in ("approve", "reject"):
        raise ProcurementToolError(f"Invalid action '{action}'. Must be 'approve' or 'reject'.")

    doc_uuid = uuid.UUID(document_id)
    svc = ApprovalService(db)
    wf = await svc.get_workflow_for_document(org_id, document_type, doc_uuid)
    if not wf:
        raise ProcurementToolError(
            f"No active approval workflow found for {document_type} {document_id}."
        )

    try:
        wf = await svc.decide(
            workflow_id=wf.id,
            org_id=org_id,
            action=action,
            user_id=user_id,
            comments=comments,
        )
    except WorkflowNotFound:
        raise ProcurementToolError(f"Workflow {wf.id} not found.")
    except NotPendingStep as exc:
        raise ProcurementToolError(str(exc))

    logger.info(
        "procurement_tool_approval_decided",
        document_type=document_type,
        document_id=document_id,
        action=action,
        workflow_status=wf.status,
    )

    return {
        "action": "approve_document",
        "document_type": document_type,
        "document_id": document_id,
        "decision": action,
        "workflow_id": str(wf.id),
        "workflow_status": wf.status,
        "step": wf.current_step,
        "comments": comments,
    }


# ── Phase 2 Tools: Sourcing & Bid Comparison ──────────────────────────────────

async def tool_create_rfx(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: str | None,
    title: str,
    rfx_type: str = "rfq",
    description: str | None = None,
    material_request_id: str | None = None,
    supplier_ids: list[str] | None = None,
    criteria: list[dict[str, Any]] | None = None,
    deadline_days: int = 14,
    category: str | None = None,
    auto_publish: bool = True,
) -> dict[str, Any]:
    """
    Create an RFx sourcing event (optionally publish and invite suppliers).
    """
    from datetime import datetime, timedelta, timezone
    from app.modules.rfx.schemas import EvaluationCriterion, RFxEventCreate
    from app.modules.rfx.service import RFxService

    mr_uuid = uuid.UUID(material_request_id) if material_request_id else None
    sup_uuids = [uuid.UUID(s) for s in supplier_ids] if supplier_ids else []

    eval_criteria: list[EvaluationCriterion] = []
    if criteria:
        for c in criteria:
            eval_criteria.append(
                EvaluationCriterion(
                    criterion=c.get("criterion", "Quality"),
                    weight=float(c.get("weight", 25.0)),
                    description=c.get("description"),
                )
            )
    else:
        eval_criteria = [
            EvaluationCriterion(criterion="Price", weight=40.0, description="Cost competitiveness"),
            EvaluationCriterion(criterion="Quality", weight=25.0, description="Specifications compliance"),
            EvaluationCriterion(criterion="Delivery", weight=20.0, description="Fulfillment lead time"),
            EvaluationCriterion(criterion="Risk", weight=15.0, description="Supplier risk assessment rating"),
        ]

    deadline = datetime.now(timezone.utc) + timedelta(days=deadline_days)
    svc = RFxService(db)
    data = RFxEventCreate(
        rfx_type=rfx_type,  # type: ignore[arg-type]
        title=title,
        description=description,
        material_request_id=mr_uuid,
        category=category,
        evaluation_criteria=eval_criteria,
        submission_deadline=deadline,
        supplier_ids=sup_uuids,
    )
    rfx = await svc.create_rfx(org_id, data, user_id=user_id)

    if auto_publish:
        try:
            rfx = await svc.publish_rfx(rfx.id, org_id, user_id=user_id)
        except Exception as exc:
            logger.warning("tool_create_rfx_publish_failed", error=str(exc))

    return {
        "action": "create_rfx",
        "rfx_id": str(rfx.id),
        "rfx_number": rfx.rfx_number,
        "rfx_type": rfx.rfx_type,
        "title": rfx.title,
        "status": rfx.status,
        "submission_deadline": rfx.submission_deadline.isoformat() if rfx.submission_deadline else None,
        "invited_supplier_count": len(rfx.invitations or []),
        "criteria_count": len(rfx.evaluation_criteria or []),
    }


async def tool_compare_quotations(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: str | None = None,
    rfx_id: str,
) -> dict[str, Any]:
    """
    Run deterministic bid comparison on all supplier quotations for an RFx event.
    """
    from app.modules.rfx.models import RFxEvent
    from app.modules.rfx.service import RFxNotFound, RFxService

    svc = RFxService(db)

    # Allow looking up by UUID string or RFx number (e.g. "RFQ-2026-0001")
    target_uuid: uuid.UUID | None = None
    try:
        target_uuid = uuid.UUID(rfx_id)
    except ValueError:
        stmt = select(RFxEvent.id).where(
            RFxEvent.org_id == org_id,
            RFxEvent.rfx_number.ilike(rfx_id.strip()),
            RFxEvent.deleted_at.is_(None),
        )
        target_uuid = (await db.execute(stmt)).scalar_one_or_none()

    if not target_uuid:
        raise ProcurementToolError(f"RFx event '{rfx_id}' not found.")

    try:
        result = await svc.compare_bids(target_uuid, org_id)
    except RFxNotFound:
        raise ProcurementToolError(f"RFx event '{rfx_id}' not found.")

    return {
        "action": "compare_quotations",
        "rfx_id": str(result.rfx_id),
        "rfx_number": result.rfx_number,
        "rfx_type": result.rfx_type,
        "title": result.title,
        "status": result.status,
        "total_bids": len(result.bids),
        "recommended_bid_id": str(result.recommended_response_id) if result.recommended_response_id else None,
        "recommended_supplier_id": str(result.recommended_supplier_id) if result.recommended_supplier_id else None,
        "recommended_supplier_name": result.recommended_supplier_name,
        "recommendation_summary": result.recommendation_summary,
        "bids": [b.model_dump() for b in result.bids],
    }
