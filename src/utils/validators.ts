import { z } from 'zod';
import { MemoryType, MemorySource, MemoryTier } from '../types/memory.js';

export const MemoryContextSchema = z.object({
  project: z.string().optional(),
  file_path: z.string().optional(),
  language: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

export const StoreMemorySchema = z.object({
  content: z.string().min(1, 'Content cannot be empty'),
  type: z.nativeEnum(MemoryType),
  tier: z.nativeEnum(MemoryTier).optional(),
  source: z.nativeEnum(MemorySource),
  context: MemoryContextSchema.optional(),
  importance: z.enum(['low', 'medium', 'high', 'critical']).optional(),
});

export const SearchFiltersSchema = z.object({
  time_range: z
    .object({
      start: z.string().datetime(),
      end: z.string().datetime(),
    })
    .optional(),
  types: z.array(z.nativeEnum(MemoryType)).optional(),
  projects: z.array(z.string()).optional(),
  min_importance: z.number().min(0).max(1).optional(),
  tiers: z.array(z.nativeEnum(MemoryTier)).optional(),
});

export const SearchMemorySchema = z.object({
  query: z.string().min(1, 'Query cannot be empty'),
  filters: SearchFiltersSchema.optional(),
  limit: z.number().min(1).max(100).default(10),
  include_related: z.boolean().default(false),
});
