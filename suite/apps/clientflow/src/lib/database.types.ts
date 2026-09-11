// GENERATED FILE — do not edit by hand (ADR-006).
// Source: applied migration chain in suite/supabase/migrations, introspected by
// suite/supabase/scripts/gen-types.mjs. Regenerate: npm run db:types
// Verify no drift: npm run db:types:check

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      cf_clients: {
        Row: {
          id: string
          workspace_id: string
          name: string
          contact_name: string | null
          contact_email: string | null
          archived_at: string | null
          created_by: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          workspace_id: string
          name: string
          contact_name?: string | null
          contact_email?: string | null
          archived_at?: string | null
        }
        Update: {
          name?: string
          contact_name?: string | null
          contact_email?: string | null
          archived_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "cf_clients_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "cf_clients_workspace_id_fkey"
            columns: ["workspace_id"]
            isOneToOne: false
            referencedRelation: "platform_workspaces"
            referencedColumns: ["id"]
          },
        ]
      }
      cf_projects: {
        Row: {
          id: string
          workspace_id: string
          client_id: string
          name: string
          description: string
          status: Database["public"]["Enums"]["cf_project_status"]
          due_date: string | null
          version: number
          created_by: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          workspace_id: string
          client_id: string
          name: string
          description?: string
          status?: Database["public"]["Enums"]["cf_project_status"]
          due_date?: string | null
          version?: number
        }
        Update: {
          client_id?: string
          name?: string
          description?: string
          status?: Database["public"]["Enums"]["cf_project_status"]
          due_date?: string | null
          version?: number
        }
        Relationships: [
          {
            foreignKeyName: "cf_projects_client_same_workspace_fkey"
            columns: ["workspace_id", "client_id"]
            isOneToOne: false
            referencedRelation: "cf_clients"
            referencedColumns: ["workspace_id", "id"]
          },
          {
            foreignKeyName: "cf_projects_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "cf_projects_workspace_id_fkey"
            columns: ["workspace_id"]
            isOneToOne: false
            referencedRelation: "platform_workspaces"
            referencedColumns: ["id"]
          },
        ]
      }
      platform_members: {
        Row: {
          workspace_id: string
          user_id: string
          role: Database["public"]["Enums"]["platform_role"]
          created_at: string
          updated_at: string
        }
        Insert: never // authenticated has no INSERT grant; use an rpc function
        Update: never // authenticated has no UPDATE grant
        Relationships: [
          {
            foreignKeyName: "platform_members_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "platform_members_workspace_id_fkey"
            columns: ["workspace_id"]
            isOneToOne: false
            referencedRelation: "platform_workspaces"
            referencedColumns: ["id"]
          },
        ]
      }
      platform_profiles: {
        Row: {
          id: string
          display_name: string
          created_at: string
          updated_at: string
        }
        Insert: never // authenticated has no INSERT grant; use an rpc function
        Update: {
          display_name?: string
        }
        Relationships: [
          {
            foreignKeyName: "platform_profiles_id_fkey"
            columns: ["id"]
            isOneToOne: true
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      platform_workspaces: {
        Row: {
          id: string
          app: Database["public"]["Enums"]["platform_app"]
          name: string
          created_by: string
          created_at: string
          updated_at: string
        }
        Insert: never // authenticated has no INSERT grant; use an rpc function
        Update: {
          name?: string
        }
        Relationships: [
          {
            foreignKeyName: "platform_workspaces_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      platform_create_workspace: {
        Args: {
          target_app: Database["public"]["Enums"]["platform_app"]
          ws_name: string
        }
        Returns: string
      }
      platform_ensure_profile: {
        Args: {
          name: string
        }
        Returns: undefined
      }
      platform_has_role: {
        Args: {
          target_workspace: string
          expected_app: Database["public"]["Enums"]["platform_app"]
          allowed_roles: Database["public"]["Enums"]["platform_role"][]
        }
        Returns: boolean
      }
      platform_is_member: {
        Args: {
          target_workspace: string
        }
        Returns: boolean
      }
      platform_is_staff: {
        Args: {
          target_workspace: string
          expected_app: Database["public"]["Enums"]["platform_app"]
        }
        Returns: boolean
      }
    }
    Enums: {
      cf_project_status: "planned" | "active" | "review" | "completed" | "archived"
      platform_app: "clientflow" | "supportdesk" | "invoicehub"
      platform_role: "owner" | "admin" | "member" | "client"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type PublicSchema = Database["public"]

export type Tables<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Row"]
export type TablesInsert<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Insert"]
export type TablesUpdate<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Update"]
export type Enums<T extends keyof PublicSchema["Enums"]> = PublicSchema["Enums"][T]
export type Functions<T extends keyof PublicSchema["Functions"]> = PublicSchema["Functions"][T]

export const Constants = {
  public: {
    Enums: {
      cf_project_status: ["planned", "active", "review", "completed", "archived"],
      platform_app: ["clientflow", "supportdesk", "invoicehub"],
      platform_role: ["owner", "admin", "member", "client"],
    },
  },
} as const
