import React from "react";

interface SubscriptionPurchaseProps {
    params: { months: string }
}

const SubscriptionPurchase: React.FC<SubscriptionPurchaseProps> = ({params}) => {
    const months = Number(params.months);
    // Telegram.WebApp.openLink("https://google.com", {try_instant_view: true})

    return <div/>
};

export default SubscriptionPurchase;
