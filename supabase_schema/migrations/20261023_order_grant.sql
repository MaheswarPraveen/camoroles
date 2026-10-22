-- Marks a Razorpay order paid and extends the buyer's Pro access in one transaction.
-- Used by both the checkout page (/api/checkout/verify) and the Razorpay webhook, so whichever
-- arrives first grants access and the other is a no-op. Safe to call any number of times.
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

  if v_order.status = 'paid' then
    select unlimited_until into v_until from user_entitlements where user_id = v_order.user_id;
    return jsonb_build_object('ok', true, 'already', true, 'user_id', v_order.user_id, 'unlimited_until', v_until);
  end if;

  v_days := case v_order.plan when 'week' then 7 else 30 end;

  insert into user_entitlements (user_id, unlimited_until)
  values (v_order.user_id, now() + make_interval(days => v_days))
  on conflict (user_id) do update
    set unlimited_until = greatest(coalesce(user_entitlements.unlimited_until, now()), now()) + make_interval(days => v_days)
  returning unlimited_until into v_until;

  update job_orders set status = 'paid', payment_id = coalesce(p_payment, payment_id) where id = p_order;

  return jsonb_build_object('ok', true, 'already', false, 'user_id', v_order.user_id, 'unlimited_until', v_until);
end;
$$;

revoke all on function public.job_order_grant(text, text) from public, anon, authenticated;
