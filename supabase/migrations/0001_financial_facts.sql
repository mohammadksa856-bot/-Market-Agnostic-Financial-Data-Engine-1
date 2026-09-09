create table if not exists public.financial_facts (
    company_id text not null,
    ticker text not null,
    market text not null check (market in ('SA', 'US')),
    metric text not null,
    display_name text,
    category text,
    statement text,
    period_end date not null,
    period_kind text not null check (period_kind in (
        'instant', 'quarter', 'ytd', 'fy', 'ttm', 'as_of', 'daily', 'event'
    )),
    fiscal_year integer,
    fiscal_quarter integer check (fiscal_quarter between 1 and 4),
    scope text not null default 'consolidated',
    dimensions jsonb not null default '{}'::jsonb,
    dimensions_key text not null default '',
    value numeric,
    value_text text,
    value_type text not null,
    currency text,
    unit text,
    is_calculated boolean not null default false,
    calculation text,
    quality_score numeric,
    source_url text,
    source_key text,
    filed_at timestamptz,
    report_page integer,
    report_table text,
    extraction_label text,
    extraction_value text,
    mapping_confidence numeric,
    mapping_method text,
    archived_path text,
    archived_sha256 text,
    engine_version text not null,
    synced_at timestamptz not null,
    primary key (company_id, metric, period_end, period_kind, scope, dimensions_key),
    check (value is not null or value_text is not null)
);

create index if not exists financial_facts_company_period_idx
    on public.financial_facts (market, ticker, period_end desc, period_kind);
create index if not exists financial_facts_metric_idx
    on public.financial_facts (metric, period_end desc);
create index if not exists financial_facts_category_idx
    on public.financial_facts (company_id, category, period_end desc);
create index if not exists financial_facts_dimensions_idx
    on public.financial_facts using gin (dimensions);

alter table public.financial_facts enable row level security;

-- Keep any existing authenticated content-manager policy intact when this
-- migration is applied to an application database. Public clients remain
-- strictly read-only; the engine publishes with the server-only service role.
revoke insert, update, delete, truncate, references, trigger
    on public.financial_facts from anon;
grant select on public.financial_facts to anon, authenticated;

drop policy if exists "public read-only financial facts" on public.financial_facts;
create policy "public read-only financial facts"
    on public.financial_facts for select
    to anon, authenticated
    using (true);

comment on table public.financial_facts is
    'Read-only consumer projection published by the Market-Agnostic Financial Data Engine.';
