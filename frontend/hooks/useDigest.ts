// hooks/useDigest.ts · T27
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface DigestItem {
  id: string;
  rank: number;
  title: string;
  summary: string | null;
  quality_score: number;
  type: 'model' | 'application';
  region: 'domestic' | 'overseas';
  category: string;
  source_name: string;
  source_url: string;
  published_at: string | null;
  estimated_minutes: number;
  is_read: boolean;
  is_bookmarked: boolean;
  related_item_ids: string[];
}

interface DigestToday {
  date: string;
  vibe: string | null;
  item_count: number;
  items: DigestItem[];
}

interface DigestSource {
  id: string;
  user_id: string | null;
  name: string;
  url: string;
  type: 'model' | 'application';
  region: 'domestic' | 'overseas';
  enabled: boolean;
  is_default: boolean;
}

interface DigestSettings {
  user_id: string;
  push_hour: number;
  push_minute: number;
  push_timezone: string;
  email_enabled: boolean;
  interested_tags: string[];
  blocked_tags: string[];
}

export function useDigestToday() {
  return useQuery<DigestToday>({
    queryKey: ['digest', 'today'],
    queryFn: async () => {
      const res = await fetch('/api/digest/today');
      if (!res.ok) throw new Error('Failed to fetch today');
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useDigestBookmarks(filter: 'all' | 'model' | 'application' = 'all') {
  return useQuery<{ total: number; items: DigestItem[] }>({
    queryKey: ['digest', 'bookmarks', filter],
    queryFn: async () => {
      const url = filter === 'all' ? '/api/digest/bookmarks' : `/api/digest/bookmarks?type=${filter}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch bookmarks');
      return res.json();
    },
  });
}

export function useAddBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (item_id: string) => {
      const res = await fetch('/api/digest/bookmarks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id }),
      });
      if (!res.ok) throw new Error('Failed to add bookmark');
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['digest', 'bookmarks'] });
      qc.invalidateQueries({ queryKey: ['digest', 'today'] });
    },
  });
}

export function useRemoveBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (item_id: string) => {
      const res = await fetch(`/api/digest/bookmarks/${item_id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to remove bookmark');
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['digest', 'bookmarks'] });
    },
  });
}

export function useHideItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (params: { item_id: string; reason: string; topic_keywords: string[] }) => {
      const res = await fetch('/api/digest/hide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!res.ok) throw new Error('Failed to hide');
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['digest'] }),
  });
}

export function useMarkRead() {
  return useMutation({
    mutationFn: async (params: { item_id: string; duration_sec: number }) => {
      const res = await fetch('/api/digest/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!res.ok) throw new Error('Failed to mark read');
      return res.json();
    },
  });
}

export function useDigestSources() {
  return useQuery<{ system_count: number; user_count: number; items: DigestSource[] }>({
    queryKey: ['digest', 'sources'],
    queryFn: async () => {
      const res = await fetch('/api/digest/sources');
      if (!res.ok) throw new Error('Failed to fetch sources');
      return res.json();
    },
  });
}

export function useAddDigestSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (source: { name: string; url: string; type: 'model' | 'application'; region: 'domestic' | 'overseas' }) => {
      const res = await fetch('/api/digest/sources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(source),
      });
      if (!res.ok) throw new Error('Failed to add source');
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['digest', 'sources'] }),
  });
}

export function usePatchDigestSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (params: { id: string; enabled?: boolean; name?: string }) => {
      const { id, ...body } = params;
      const res = await fetch(`/api/digest/sources/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed to patch source');
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['digest', 'sources'] }),
  });
}

export function useDigestSettings() {
  return useQuery<DigestSettings>({
    queryKey: ['digest', 'settings'],
    queryFn: async () => {
      const res = await fetch('/api/digest/settings');
      if (!res.ok) throw new Error('Failed to fetch settings');
      return res.json();
    },
  });
}

export function useUpdateDigestSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (patch: Partial<DigestSettings>) => {
      const res = await fetch('/api/digest/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error('Failed to update settings');
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['digest', 'settings'] }),
  });
}
