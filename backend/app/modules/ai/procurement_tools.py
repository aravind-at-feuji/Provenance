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
