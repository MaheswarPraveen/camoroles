-- Guest checkout: buy Pro without signing in. Pro is held by a browser device id and moves to the
-- account the first time that browser signs in.

alter table public.job_orders alter column user_id drop not null;
alter table public.job_orders add column if not exists device_id text;
alter table public.job_orders drop constraint if exists job_orders_owner_present;
alter table public.job_orders add constraint job_orders_owner_present check (user_id is not null or device_id is not null);

create table if not exists public.guest_entitlements (
  device_id text primary key,
  unlimited_until timestamptz not null,
  created_at timestamptz not null default now()
);
alter table public.guest_entitlements enable row level security;   -- server only

-- Marks an order paid and extends Pro for whoever owns it (account or guest device). Safe to repeat.
create or replace function public.job_order_grant(p_order text, p_payment text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_order job_orders%rowtype;
  v_days int;
  v_until timestamptz;
begin
  select * into v_order from job_orders where id = p_order for update;
  if not found then
    return jsonb_build_object('ok', false, 'error', 'order_not_found');
  end if;
  v_days := case v_order.plan when 'week' then 7 else 30 end;

  if v_order.status = 'paid' then
    if v_order.user_id is not null then
      select unlimited_until into v_until from user_entitlements where user_id = v_order.user_id;
    else
      select unlimited_until into v_until from guest_entitlements where device_id = v_order.device_id;
    end if;
    return jsonb_build_object('ok', true, 'already', true, 'unlimited_until', v_until);
  end if;

  if v_order.user_id is not null then
    insert into user_entitlements (user_id, unlimited_until)
    values (v_order.user_id, now() + make_interval(days => v_days))
    on conflict (user_id) do update
      set unlimited_until = greatest(coalesce(user_entitlements.unlimited_until, now()), now()) + make_interval(days => v_days)
    returning unlimited_until into v_until;
  else
    insert into guest_entitlements (device_id, unlimited_until)
    values (v_order.device_id, now() + make_interval(days => v_days))
    on conflict (device_id) do update
      set unlimited_until = greatest(guest_entitlements.unlimited_until, now()) + make_interval(days => v_days)
    returning unlimited_until into v_until;
  end if;

  update job_orders set status = 'paid', payment_id = coalesce(p_payment, payment_id) where id = p_order;
  return jsonb_build_object('ok', true, 'already', false, 'unlimited_until', v_until);
end;
$$;

-- When a browser that bought Pro as a guest signs in, its remaining Pro time moves to the account.
create or replace function public.claim_guest_pro(p_user uuid, p_device text)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare
  v_guest timestamptz;
  v_until timestamptz;
begin
  delete from guest_entitlements where device_id = p_device and unlimited_until > now()
  returning unlimited_until into v_guest;
  if v_guest is not null then
    insert into user_entitlements (user_id, unlimited_until) values (p_user, v_guest)
    on conflict (user_id) do update
      set unlimited_until = greatest(coalesce(user_entitlements.unlimited_until, now()), now()) + (v_guest - now());
    update job_orders set user_id = p_user where device_id = p_device and user_id is null;
  end if;
  select unlimited_until into v_until from user_entitlements where user_id = p_user;
  return v_until;
end;
$$;

revoke all on function public.job_order_grant(text, text) from public, anon, authenticated;
revoke all on function public.claim_guest_pro(uuid, text) from public, anon, authenticated;
