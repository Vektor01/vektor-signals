const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const PRICE_TO_TIER = {
  'price_1TDOtF2QjRYoJfPkvKXvq6r4': 'standard',
  'price_1TDPQG2QjRYoJfPkC2doh5BO': 'standard',
  'price_1TDmhf2QjRYoJfPkUietPgLS': 'vip',
};

exports.handler = async (event) => {
  const sig = event.headers['stripe-signature'];
  let stripeEvent;

  try {
    stripeEvent = stripe.webhooks.constructEvent(
      event.body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    return { statusCode: 400, body: `Webhook Error: ${err.message}` };
  }

  const { type, data } = stripeEvent;

  if (type === 'checkout.session.completed') {
    const session    = data.object;
    const email      = session.customer_details?.email;
    const customerId = session.customer;
    const subId      = session.subscription;
    let tier = 'standard';
    if (subId) {
      try {
        const sub = await stripe.subscriptions.retrieve(subId);
        const priceId = sub.items.data[0]?.price?.id;
        tier = PRICE_TO_TIER[priceId] || 'standard';
      } catch (e) {}
    }
    if (email) {
      await supabase.from('subscribers').upsert({
        email, tier, active: true,
        stripe_customer_id: customerId,
        stripe_sub_id: subId,
        cancelled_at: null,
      }, { onConflict: 'email' });
    }
  }

  if (type === 'customer.subscription.deleted') {
    await supabase.from('subscribers')
      .update({ active: false, cancelled_at: new Date().toISOString() })
      .eq('stripe_sub_id', data.object.id);
  }

  if (type === 'invoice.payment_failed') {
    await supabase.from('subscribers')
      .update({ active: false })
      .eq('stripe_customer_id', data.object.customer);
  }

  if (type === 'customer.subscription.updated') {
    if (data.object.status === 'active') {
      await supabase.from('subscribers')
        .update({ active: true, cancelled_at: null })
        .eq('stripe_sub_id', data.object.id);
    }
  }

  return { statusCode: 200, body: JSON.stringify({ received: true }) };
};
