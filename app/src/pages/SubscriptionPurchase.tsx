import React, {useEffect, useRef} from "react";

import styles from "./SubscriptionPurchase.module.css"
import {VerifyBlock} from "../components/subscription/purchase/VerifyBlock";
import WideButton from "../components/common/Buttons/WideButton";
import {useParams} from "wouter";

import Eagle from "../assets/icons/eagle.svg";
import Money from "../assets/subscription/money.svg";
import {Bank, TARIFF_PRICES_NORMALIZED} from "../utils/consts";
import {fetchPurchaseLink} from "../api/base";

const SubscriptionPurchase: React.FC = () => {
    const purchaseBlockRef = useRef<HTMLDivElement>(null);
    const ticketSeparatorRef = useRef<HTMLDivElement>(null);
    const isFetchingLink = useRef(false);

    const params = useParams<{ months: string }>();
    const months = Number(params.months);
    const [step, setStep] = React.useState(1);
    const [bank, setBank] = React.useState<Bank>("ru");
    const [link, setLink] = React.useState<string>("");

    const title = months === 1 ? "1 мес." : months === 3 ? "3 мес." : "год";
    const price = TARIFF_PRICES_NORMALIZED[months];

    const receivePurchaseLink = async () => {
        if (link !== "") return;
        try {
            if (isFetchingLink.current) return;
            isFetchingLink.current = true;

            const link = await fetchPurchaseLink(months, bank, "foo@bar.baz")
            setLink(link)
        } finally {
            isFetchingLink.current = false;
        }
    }

    useEffect(() => {
        function calculateTicketSeparatorTop() {
            if (ticketSeparatorRef.current && purchaseBlockRef.current) {
                const block = purchaseBlockRef.current.getBoundingClientRect();
                const separator = ticketSeparatorRef.current.getBoundingClientRect();
                const offset = separator.top - block.top + separator.height / 2;

                purchaseBlockRef.current.style.setProperty('--separator-top', `${offset}px`);
            }
        }

        if (step === 1) {
            calculateTicketSeparatorTop();
            window.addEventListener('resize', calculateTicketSeparatorTop);
        }

        return () => window.removeEventListener('resize', calculateTicketSeparatorTop);
    }, [step]);

    useEffect(() => {
        if (link !== "") Telegram.WebApp.openLink(link, {try_instant_view: true})
    }, [link]);

    return <div className={styles.container}>
        <div className={styles.stepsBlock}>
            <div className={styles.stepBlock}>
                <div className={styles.selectedStep}/>
                <span className={styles.purple}>//Выбор</span>
            </div>
            <div className={styles.stepBlock}>
                <div className={`${step >= 2 ? styles.selectedStep : styles.step}`}/>
                <span className={`${step >= 2 ? styles.purple : ""}`}>//Проверка</span>
            </div>
            <div className={styles.stepBlock}>
                <div className={`${step >= 3 ? styles.selectedStep : styles.step}`}/>
                <span className={`${step >= 3 ? styles.purple : ""}`}>//Оплата</span>
            </div>
        </div>
        {step === 1 && (
            <div ref={purchaseBlockRef} className={styles.purchaseBlock} style={{"--separator-top": "-100px"} as React.CSSProperties}>
                <div className={styles.purchaseHeader}>
                    <div className={styles.purchaseTitle}>Наименование товара</div>
                    <div className={styles.purchaseItem}>
                        <Eagle height="17px" width="17px" color="#7211F8"/>
                        <span>{`Cardinal Pro / ${title}`}</span>
                    </div>
                </div>
                <div className={styles.purchaseSeparator}>
                    <img height="1px" width="auto" src="/assets/subscription/purchase/separator.svg" alt=" "/>
                </div>
                <div className={styles.bankBlock}>
                    <div className={styles.bankTitle}>
                        Метод оплаты
                    </div>
                    <div className={`${bank === "ru" ? styles.bankSelected : styles.bankNonSelected}`} onClick={() => setBank("ru")}>
                        Банк РФ
                    </div>
                    <div className={`${bank === "external" ? styles.bankSelected : styles.bankNonSelected}`} onClick={() => setBank("external")}>
                        Иностранный банк
                    </div>
                </div>
                <div ref={ticketSeparatorRef} className={styles.ticketSeparator}/>
                <div className={styles.purchasePrice}>
                    <span className={styles.priceTitle}>Стоимость</span>
                    <span className={styles.priceValue}>{price} RUB</span>
                </div>
                <div style={{flex: 1}}/>
                <WideButton color="#7211F8" text={
                    <div className={styles.nextStepButton}>
                        <img height="15px" width="17px" src="/assets/finder/task/forward.svg" alt=" "/>
                        <span style={{color: "white"}}>Далее</span>
                    </div>
                } buttonStyle={{borderRadius: 14, height: 47, marginTop: 55}} onClick={() => setStep(2)}/>
            </div>
        )}
        {step === 2 && (
            <div className={styles.verifyBlock}>
                <div className={styles.logo}>
                    <img height="18px" width="72px" src="/assets/subscription/purchase/logo.svg" alt=" "/>
                </div>
                <div className={styles.verifyTitle}>
                    Убедитесь, что введенные данные верны
                </div>
                <div className={styles.verifyBlocks}>
                    <VerifyBlock icon={<img height="15px" width="15px" src="/assets/subscription/purchase/title.svg" alt=" "/>}
                                 title="Наименование товара"
                                 value={`Cardinal Pro / ${title}`}/>
                    <VerifyBlock icon={<img height="12px" width="16px" src="/assets/subscription/purchase/card.svg" alt=" "/>} title="Метод оплаты"
                                 value={bank === "ru" ? "Банк РФ" : "Иностранный банк"}/>
                    <VerifyBlock icon={<img height="11px" width="16px" src="/assets/subscription/purchase/price.svg" alt=" "/>} title="Стоимость"
                                 value={price}/>
                </div>

                <div className={styles.verifying}>
                    <img height="69px" width="122px" src="/assets/logo.svg" alt=" " className={styles.loading}/>
                </div>
                <div className={styles.buttons}>
                    <WideButton color="#7211F8" text={
                        <div className={styles.subscriptionButton}>
                            <Money height="13px" width="19px" color="white"/>
                            Перейти к оплате
                        </div>
                    } buttonStyle={{borderRadius: 14, height: 47}} style={{}} onClick={() => {
                        void receivePurchaseLink();
                        setStep(3);
                    }}/>
                    <WideButton color="#7211F833" textColor="#7211F8" text="Назад" buttonStyle={{borderRadius: 14, height: 47}}
                                onClick={() => setStep(1)}/>
                </div>
            </div>
        )}
        {step === 3 && (
            <div className={styles.checkBlock}>
                <div className={styles.logo}>
                    <img height="18px" width="72px" src="/assets/subscription/purchase/logo.svg" alt=" "/>
                </div>
                <img height="91px" width="160px" src="/assets/logo.svg" alt=" " className={styles.loading}/>
                <div className={styles.checkTitle}>
                    <span>
                        <span className={styles.purple}>//</span>
                        <span>Ожидание подтверждения оплаты...</span>
                    </span>
                </div>
                <WideButton color={"transparent"} text={
                    <div className={styles.checkLinkButton}>
                        <img height="15px" width="17px" src="/assets/subscription/purchase/link.svg" alt=" "/>
                        <span className={styles.checkLink}>Открыть страницу оплаты</span>
                    </div>
                } buttonStyle={{height: 45}} style={{
                    borderRadius: 14,
                    border: "1px solid #7211F8"
                }} onClick={link === "" ? undefined : () => Telegram.WebApp.openLink(link, {try_instant_view: true})}/>
            </div>
        )}
    </div>
};

export default SubscriptionPurchase;
