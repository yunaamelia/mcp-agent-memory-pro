export enum MemoryTier {
  SHORT = 'short',
  WORKING = 'working',
  LONG = 'long',
}

export enum MemoryType {
  CODE = 'code',
  COMMAND = 'command',
  CONVERSATION = 'conversation',
  NOTE = 'note',
  EVENT = 'event',
}

export enum MemorySource {
  IDE = 'ide',
  TERMINAL = 'terminal',
  MANUAL = 'manual',
}

export interface MemoryContext {
  project?: string;
  file_path?: string;
  language?: string;
  tags?: string[];
}

export interface Memory {
  id: string;
  tier: MemoryTier;
  type: MemoryType;
  source: MemorySource;

  // Content
  content: string;
  content_hash?: string;

  // Context
  context: MemoryContext;

  // Metadata
  timestamp?: number;
  entities?: string[];

  // Intelligence
  importance: 'low' | 'medium' | 'high' | 'critical';
  importance_score?: number;
  access_count?: number;
  last_accessed?: string;

  // Lifecycle
  created_at: string;
  updated_at: string;
  promoted_from?: string;
  archived?: boolean;
}

export interface SearchFilters {
  time_range?: {
    start: Date;
    end: Date;
  };
  types?: MemoryType[];
  projects?: string[];
  min_importance?: number;
  tiers?: MemoryTier[];
}

export interface SearchResult {
  memory: Memory;
  score: number;
  distance: number;
}

export interface StoreMemoryParams {
  content: string;
  type: MemoryType;
  tier?: MemoryTier; // Optional, defaults to SHORT
  source: MemorySource;
  context?: MemoryContext;
  importance?: 'low' | 'medium' | 'high' | 'critical';
}

export interface SearchMemoryParams {
  query: string;
  filters?: SearchFilters;
  limit?: number;
  include_related?: boolean;
}
