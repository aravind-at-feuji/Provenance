/**
 * src/lib/store/conversation-store.ts — State management for Agent Trace conversation history.
 *
 * Persists all past conversations, active conversation selection,
 * message threads, execution traces, and citations in local storage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage } from "@/components/investigate/agent-trace-workspace";

export interface AgentConversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

interface ConversationState {
  conversations: AgentConversation[];
  activeConversationId: string | null;

  // Actions
  createConversation: (title?: string) => string;
  selectConversation: (id: string) => void;
  updateActiveMessages: (messages: ChatMessage[]) => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, newTitle: string) => void;
  clearAllConversations: () => void;
}

function generateTitleFromMessage(content: string): string {
  const clean = content.replace(/^[#*\s-]+/, "").trim();
  if (!clean) return "New Conversation";
  if (clean.length <= 32) return clean;
  return clean.slice(0, 30).trim() + "...";
}

export const useConversationStore = create<ConversationState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,

      createConversation: (title?: string) => {
        const id = `conv-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
        const now = new Date().toISOString();
        const newConv: AgentConversation = {
          id,
          title: title || "New Conversation",
          createdAt: now,
          updatedAt: now,
          messages: [],
        };

        set((state) => ({
          conversations: [newConv, ...state.conversations],
          activeConversationId: id,
        }));

        return id;
      },

      selectConversation: (id: string) => {
        set({ activeConversationId: id });
      },

      updateActiveMessages: (messages: ChatMessage[]) => {
        const { activeConversationId, conversations } = get();
        const now = new Date().toISOString();

        if (!activeConversationId) {
          // If no active conversation exists, create one automatically
          const firstUserMsg = messages.find((m) => m.role === "user");
          const title = firstUserMsg ? generateTitleFromMessage(firstUserMsg.content) : "New Conversation";
          const newId = `conv-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
          const newConv: AgentConversation = {
            id: newId,
            title,
            createdAt: now,
            updatedAt: now,
            messages,
          };
          set({
            conversations: [newConv, ...conversations],
            activeConversationId: newId,
          });
          return;
        }

        set((state) => {
          const updated = state.conversations.map((conv) => {
            if (conv.id !== activeConversationId) return conv;

            // Auto-update title from the first user query if still generic
            let title = conv.title;
            if (title === "New Conversation") {
              const firstUserMsg = messages.find((m) => m.role === "user");
              if (firstUserMsg) {
                title = generateTitleFromMessage(firstUserMsg.content);
              }
            }

            return {
              ...conv,
              title,
              updatedAt: now,
              messages,
            };
          });

          // Sort by updatedAt descending
          updated.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());

          return { conversations: updated };
        });
      },

      deleteConversation: (id: string) => {
        set((state) => {
          const remaining = state.conversations.filter((c) => c.id !== id);
          let nextActiveId = state.activeConversationId;
          if (state.activeConversationId === id) {
            nextActiveId = remaining.length > 0 ? remaining[0].id : null;
          }
          return {
            conversations: remaining,
            activeConversationId: nextActiveId,
          };
        });
      },

      renameConversation: (id: string, newTitle: string) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title: newTitle.trim() || c.title } : c
          ),
        }));
      },

      clearAllConversations: () => {
        set({ conversations: [], activeConversationId: null });
      },
    }),
    {
      name: "provenance-agent-conversations",
      partialize: (state) => ({
        conversations: state.conversations,
        activeConversationId: state.activeConversationId,
      }),
    }
  )
);

export function formatRelativeTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return "Just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay === 1) return "Yesterday";
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}
