import styles from "./SubscriptionPurchase.module.css";
import {CSSProperties, ChangeEvent, FC, useEffect, useRef, useState} from "react";

import {useLocation, useParams} from "wouter";

import {checkPurchase, fetchPurchase} from "../api/base";
import WideButton from "../components/common/Buttons/WideButton";
import Header from "../components/common/Header/Header";
import {VerifyBlock} from "../components/subscription/purchase/VerifyBlock";
import {useErrorStore} from "../store/error";
import {useStore} from "../store/store";
import {Bank, TARIFF_PRICES_NORMALIZED} from "../utils/consts";

import Eagle from "../assets/icons/eagle.svg";
import Money from "../assets/subscription/money.svg";

const SubscriptionPurchase: FC = () => {
    const [, navigate] = useLocation();
    const purchaseBlockRef = useRef<HTMLDivElement>(null);
    const ticketSeparatorRef = useRef<HTMLDivElement>(null);
    const isFetchingLink = useRef(false);
    const setSubscription = useStore((s) => s.setSubscription);

    const params = useParams<{months: string}>();
    const months = Number(params.months);
    const [step, setStep] = useState(1);
    const [bank, setBank] = useState<Bank>("ru");
    const [purchase, setPurchase] = useState<{id: string; url: string} | undefined>(undefined);
    const [email, setEmail] = useState("");
    const [emailError, setEmailError] = useState("");

    const title = months === 1 ? "1 мес." : months === 3 ? "3 мес." : "год";
    const price = TARIFF_PRICES_NORMALIZED[months];

    const receivePurchaseLink = async () => {
        if (purchase) return;
        try {
            if (isFetchingLink.current) return;
            isFetchingLink.current = true;

            setPurchase(await fetchPurchase(months, bank, email));
        } finally {
            isFetchingLink.current = false;
        }
    };

    useEffect(() => {
        function calculateTicketSeparatorTop() {
            if (ticketSeparatorRef.current && purchaseBlockRef.current) {
                const block = purchaseBlockRef.current.getBoundingClientRect();
                const separator = ticketSeparatorRef.current.getBoundingClientRect();
                const offset = separator.top - block.top + separator.height / 2;

                purchaseBlockRef.current.style.setProperty("--separator-top", `${offset}px`);
            }
        }

        if (step === 1) {
            calculateTicketSeparatorTop();
            window.addEventListener("resize", calculateTicketSeparatorTop);
        }

        return () => window.removeEventListener("resize", calculateTicketSeparatorTop);
    }, [step]);

    useEffect(() => {
        if (purchase) Telegram.WebApp.openLink(purchase.url, {try_instant_view: true});

        const handleVisibilityChange = () => {
            if (!document.hidden) {
                void checkStatus();
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, [purchase]);

    const checkStatus = async () => {
        if (!purchase) return;
        const result = await checkPurchase(purchase.id);

        if (typeof result === "string") {
            if (result === "timeout" || result === "failed")
                useErrorStore.getState().setError("exception", "Ошибка во время обработки платежа", window.location.pathname);
        } else {
            setSubscription(result);
            navigate("/");
        }
    };

    const handleEmailChange = (event: ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setEmail(value);

        if (!value) {
            setEmailError("");
            return;
        }

        const emailRegex =
            /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

        if (!emailRegex.test(value)) {
            setEmailError("Некорректный email");
        } else {
            setEmailError("");
        }
    };

    const backStep = (): boolean => {
        if (step <= 1) return false;
        setStep(step - 1);
        return true;
    };

    return (
        <div className={styles.container}>
            <Header backTo="" backoff="/subscription" icon={null} top={0} backStep={backStep} />
            <div className={styles.stepsBlock}>
                <div className={styles.stepBlock}>
                    <div className={styles.selectedStep} />
                    <span className={styles.purple}>//Выбор</span>
                </div>
                <div className={styles.stepBlock}>
                    <div className={`${step >= 2 ? styles.selectedStep : styles.step}`} />
                    <span className={`${step >= 2 ? styles.purple : ""}`}>//Проверка</span>
                </div>
                <div className={styles.stepBlock}>
                    <div className={`${step >= 3 ? styles.selectedStep : styles.step}`} />
                    <span className={`${step >= 3 ? styles.purple : ""}`}>//Оплата</span>
                </div>
            </div>
            {step === 1 && (
                <div ref={purchaseBlockRef} className={styles.purchaseBlock} style={{"--separator-top": "-100px"} as CSSProperties}>
                    <div className={styles.logo}>
                        <img height="18px" width="72px" src="/assets/subscription/purchase/logo.svg" alt=" " />
                    </div>
                    <div className={styles.purchaseHeader}>
                        <div className={styles.purchaseTitle}>Наименование товара</div>
                        <div className={styles.purchaseItem}>
                            <Eagle height="17px" width="17px" color="#7211F8" />
                            <span>{`Cardinal Pro / ${title}`}</span>
                        </div>
                    </div>
                    <div className={styles.purchaseSeparator}>
                        <img height="1px" width="auto" src="/assets/subscription/purchase/separator.svg" alt=" " />
                    </div>
                    <div className={styles.bankBlock}>
                        <div className={styles.bankTitle}>Метод оплаты</div>
                        <div className={`${bank === "ru" ? styles.bankSelected : styles.bankNonSelected}`} onClick={() => setBank("ru")}>
                            Банк РФ
                        </div>
                        <div className={`${bank === "external" ? styles.bankSelected : styles.bankNonSelected}`} onClick={() => setBank("external")}>
                            Иностранный банк
                        </div>
                    </div>
                    <div ref={ticketSeparatorRef} className={styles.ticketSeparator} />
                    <div className={styles.emailBlock}>
                        <div className={styles.emailHint}>Ваш e-mail</div>
                        <input
                            type="text"
                            id="email_text"
                            value={email}
                            onChange={handleEmailChange}
                            autoComplete={"email"}
                            placeholder={emailError || "example@gmail.com"}
                            className={`${styles.emailInput} ${emailError ? styles.inputError : ""}`}
                        />
                    </div>
                    <div className={styles.purchasePrice}>
                        <span className={styles.priceTitle}>Стоимость</span>
                        <span className={styles.priceValue}>{price} RUB</span>
                    </div>
                    <div style={{flex: 1}} />
                    <WideButton
                        color="#7211F8"
                        text={
                            <div className={styles.nextStepButton}>
                                <img height="15px" width="17px" src="/assets/finder/task/forward.svg" alt=" " />
                                <span style={{color: "#FFFFFF"}}>Далее</span>
                            </div>
                        }
                        buttonStyle={{borderRadius: 14, height: 47, marginTop: 55}}
                        onClick={emailError || email === "" ? undefined : () => setStep(2)}
                    />
                </div>
            )}
            {step === 2 && (
                <div className={styles.verifyBlock}>
                    <div className={styles.logo}>
                        <img height="18px" width="72px" src="/assets/subscription/purchase/logo.svg" alt=" " />
                    </div>
                    <div className={styles.verifyTitle}>Убедитесь, что введенные данные верны</div>
                    <div className={styles.verifyBlocks}>
                        <VerifyBlock
                            icon={<img height="15px" width="15px" src="/assets/subscription/purchase/title.svg" alt=" " />}
                            title="Наименование товара"
                            value={`Cardinal Pro / ${title}`}
                        />
                        <VerifyBlock
                            icon={<img height="12px" width="16px" src="/assets/subscription/purchase/card.svg" alt=" " />}
                            title="Метод оплаты"
                            value={bank === "ru" ? "Банк РФ" : "Иностранный банк"}
                        />
                        <VerifyBlock
                            icon={<img height="13px" width="16px" src="/assets/subscription/purchase/email.svg" alt=" " />}
                            title="Почта"
                            value={email}
                        />
                        <VerifyBlock
                            icon={<img height="11px" width="16px" src="/assets/subscription/purchase/price.svg" alt=" " />}
                            title="Стоимость"
                            value={price}
                        />
                    </div>

                    <div className={styles.verifying}>
                        <img height="69px" width="122px" src="/assets/logo.svg" alt=" " className={styles.loading} />
                    </div>
                    <div className={styles.buttons}>
                        <WideButton
                            color="#7211F8"
                            text={
                                <div className={styles.subscriptionButton}>
                                    <Money height="13px" width="19px" color="#FFFFFF" />
                                    Перейти к оплате
                                </div>
                            }
                            buttonStyle={{borderRadius: 14, height: 47}}
                            style={{}}
                            onClick={() => {
                                void receivePurchaseLink();
                                setStep(3);
                            }}
                        />
                        <WideButton color="#7211F833" textColor="#7211F8" text="Назад" buttonStyle={{borderRadius: 14, height: 47}} onClick={backStep} />
                    </div>
                </div>
            )}
            {step === 3 && (
                <div className={styles.checkBlock}>
                    <div className={styles.logo}>
                        <img height="18px" width="72px" src="/assets/subscription/purchase/logo.svg" alt=" " />
                    </div>
                    <img height="91px" width="160px" src="/assets/logo.svg" alt=" " className={styles.loading} />
                    <div className={styles.checkTitle}>
                        <span>
                            <span className={styles.purple}>//</span>
                            <span>Ожидание подтверждения оплаты...</span>
                        </span>
                    </div>
                    <WideButton
                        color={"transparent"}
                        text={
                            <div className={styles.checkLinkButton}>
                                <img height="15px" width="17px" src="/assets/subscription/purchase/link.svg" alt=" " />
                                <span className={styles.checkLink}>Открыть страницу оплаты</span>
                            </div>
                        }
                        buttonStyle={{height: 45}}
                        style={{borderRadius: 14, border: "1px solid #7211F8"}}
                        onClick={purchase ? () => Telegram.WebApp.openLink(purchase.url, {try_instant_view: true}) : undefined}
                    />
                </div>
            )}
        </div>
    );
};

export default SubscriptionPurchase;
