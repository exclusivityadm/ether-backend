-- Ether project signal support for connected Supabase projects.
-- Apply this separately inside each Supabase project Ether should keep active.
-- Intended projects now: Circa Haus and Exclusivity. Sova can use the same artifact later.

create extension if not exists pgcrypto;

create table if not exists public.ether_signals (
  id uuid primary key default gen_random_uuid(),
  app_slug text not null,
  signal_source text not null default 'ether',
  signal_kind text not null default 'heartbeat',
  lane_id text,
  status text not null default 'ok',
  app_id text,
  instance_id text,
  heartbeat_count bigint not null default 0,
  verified boolean not null default false,
  signal_payload jsonb not null default '{}'::jsonb,
  received_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists ether_signals_app_slug_received_at_idx
  on public.ether_signals (app_slug, received_at desc);

create index if not exists ether_signals_lane_received_at_idx
  on public.ether_signals (lane_id, received_at desc);

create index if not exists ether_signals_signal_payload_idx
  on public.ether_signals using gin (signal_payload);

alter table public.ether_signals enable row level security;

-- Service role bypasses RLS. No client-facing policy is intentionally added.
-- Ether should write with a server-side Supabase service role key only.

create or replace function public.ether_signal(payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  inserted_id uuid;
  incoming_app_slug text;
  incoming_source text;
  incoming_kind text;
  incoming_lane text;
  incoming_status text;
  incoming_app_id text;
  incoming_instance_id text;
  incoming_heartbeat_count bigint;
  incoming_verified boolean;
  incoming_received_at timestamptz;
begin
  incoming_app_slug := nullif(trim(coalesce(payload->>'app_slug', '')), '');
  incoming_source := nullif(trim(coalesce(payload->>'signal_source', 'ether')), '');
  incoming_kind := nullif(trim(coalesce(payload->>'signal_kind', 'heartbeat')), '');
  incoming_lane := nullif(trim(coalesce(payload->>'lane_id', '')), '');
  incoming_status := nullif(trim(coalesce(payload->>'status', 'ok')), '');
  incoming_app_id := nullif(trim(coalesce(payload->>'app_id', '')), '');
  incoming_instance_id := nullif(trim(coalesce(payload->>'instance_id', '')), '');
  incoming_heartbeat_count := coalesce(nullif(payload->>'heartbeat_count', '')::bigint, 0);
  incoming_verified := coalesce((payload->>'verified')::boolean, false);
  incoming_received_at := coalesce(nullif(payload->>'received_at', '')::timestamptz, now());

  if incoming_app_slug is null then
    raise exception 'ether_signal requires app_slug';
  end if;

  insert into public.ether_signals (
    app_slug,
    signal_source,
    signal_kind,
    lane_id,
    status,
    app_id,
    instance_id,
    heartbeat_count,
    verified,
    signal_payload,
    received_at
  ) values (
    incoming_app_slug,
    coalesce(incoming_source, 'ether'),
    coalesce(incoming_kind, 'heartbeat'),
    incoming_lane,
    coalesce(incoming_status, 'ok'),
    incoming_app_id,
    incoming_instance_id,
    incoming_heartbeat_count,
    incoming_verified,
    coalesce(payload->'signal_payload', '{}'::jsonb),
    incoming_received_at
  ) returning id into inserted_id;

  return jsonb_build_object(
    'ok', true,
    'id', inserted_id,
    'app_slug', incoming_app_slug,
    'received_at', incoming_received_at
  );
end;
$$;

comment on table public.ether_signals is 'Real Ether signal/keepalive records written by Ether into connected Supabase projects.';
comment on function public.ether_signal(jsonb) is 'Records one Ether signal payload for project keepalive, health, and operational verification.';
