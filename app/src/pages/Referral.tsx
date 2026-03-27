import styles from "./Referal.module.css";
import {FC, useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import {purchaseFromBalance} from "../api/base";
import {fetchRefs} from "../api/refs";
import BottomSection from "../components/common/BottomSection/BottomSection";
import WideButton from "../components/common/Buttons/WideButton";
import Delimiter from "../components/common/Delimiter/Delimiter";
import Header from "../components/common/Header/Header";
import {Loading} from "../components/common/Loading/Loading";
import {IncomeCalculator} from "../components/referral/IncomeCalculator";
import {RefsList} from "../components/referral/RefsList";
import {StatBlock} from "../components/referral/StatBlock";
import {useReferral} from "../store/referral";
import {useStore} from "../store/store";
import {BACKEND_BASE_URL, SUPPORT_URL, TARIFF_PRICES} from "../utils/consts";

import Mark from "../assets/icons/mark.svg";
import MoveArrow from "../assets/icons/move-arrow.svg";

const Referral: FC = () => {
    const [, navigate] = useLocation();
    const refsLoading = useRef<boolean>(false);
    const refPurchasing = useRef<boolean>(false);

    const user = useStore((s) => s.user);
    const setUser = useStore((s) => s.setUser);
    const refs = useReferral((s) => s.refs);
    const setRefs = useReferral((s) => s.setRefs);
    const setSubscription = useStore((s) => s.setSubscription);

    const copyRef = useRef<HTMLDivElement>(null);

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const run = async () => {
            if (refsLoading.current) return;
            refsLoading.current = true;

            const refs = await fetchRefs();
            setRefs(refs);
        };
        void run();
    }, [refs]);

    useEffect(() => {
        if (refs) setLoading(false);
    }, [refs]);

    if (loading) {
        return <Loading />;
    }

    const copyToClipboard = (text: string) => {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
        } else {
            fallbackCopy(text);
        }
        if (!copyRef.current) return;
        const div = copyRef.current;

        div.style.transition = "none";
        div.style.opacity = "1";
        div.classList.add("visible");

        requestAnimationFrame(() => {
            setTimeout(() => {
                div.style.transition = "opacity 2s";
                div.style.opacity = "0";
                div.classList.remove("visible");
            }, 1000);
        });
    };

    const fallbackCopy = (text: string) => {
        const input = document.createElement("input");
        input.value = text;
        input.style.position = "fixed";
        input.style.left = "-9999px";
        input.setAttribute("readonly", "");
        document.body.appendChild(input);

        input.select();
        input.setSelectionRange(0, input.value.length);

        document.execCommand("copy");
        document.body.removeChild(input);
    };

    const handlePurchaseByBalance = async () => {
        if (refPurchasing.current) return;
        refPurchasing.current = true;
        try {
            if (user!.balance < TARIFF_PRICES["1"]) return;
            const subscription = await purchaseFromBalance();
            setSubscription(subscription);
            setUser({...user!, balance: user!.balance - 4900});
        } finally {
            refPurchasing.current = false;
        }
    };

    const refBase = BACKEND_BASE_URL.replace("/api", "");
    const refLink = `${refBase}/r/${user!.user_id}`;

    return (
        <div className={styles.container}>
            <Header height={82} top={0} backTo="" icon={<img height="82px" width="76px" src="/assets/referral/header.svg" alt="CARDINAL REFERRALS" />} />

            <div className={styles.title}>
                <span>Заработай </span>
                <img height="19px" width="19px" src="/assets/referral/money-bag.svg" alt=" " />
                <span> на тех, кто ищет лиды</span>
            </div>

            <div className={styles.subtitle}>
                <span>
                    <span>Приводи в сервис новых пользователей — и получай до </span>
                    <span style={{fontWeight: 500, color: "#FFFFFF"}}>50% на баланс за каждого активного.</span>
                </span>
            </div>

            <div className={styles.stats}>
                <StatBlock
                    title="Приглашено"
                    count={refs!.length}
                    titleColor="#FFFFFF59"
                    countColor="#F2F2F2"
                    backgroundColor="#141414"
                    borderColor="#FFFFFF17"
                />
                <StatBlock
                    title="БАЛАНС"
                    count={user!.balance}
                    titleColor="#BEF81133"
                    countColor="#BEF811"
                    backgroundColor="#BEF81133"
                    borderColor="#BEF8114F"
                />
            </div>

            <div className={styles.partnerBlock}>
                <div className={styles.partnerTitle} style={{marginBottom: 6}}>
                    Твоя ссылка:
                </div>

                <div style={{position: "relative"}}>
                    <div className={styles.linkBlock} onClick={() => copyToClipboard(refLink)}>
                        <span style={{flex: 1, zIndex: 1}}>{refLink}</span>
                        <div className={styles.copyBlock}>
                            <img height="17px" width="16px" src="/assets/icons/copy.svg" alt="COPY" />
                        </div>
                    </div>
                    <div ref={copyRef} className={styles.linkCopied}>
                        <Mark height="14px" width="14px" color="#7211F8" />
                        <span>Успешно скопировано</span>
                    </div>
                </div>

                <div className={styles.partnerTitle} style={{marginTop: 12, marginLeft: 4, marginBottom: 3}}>
                    Инструкция:
                </div>

                <div className={styles.partnerInstruction}>
                    <div className={styles.dot} />
                    Скопируй свою реферальную ссылку.
                </div>
                <div className={styles.partnerInstruction} style={{paddingRight: 70}}>
                    <div className={styles.dot} />
                    Отправь её друзьям, коллегам или опубликуй в соцсетях.
                </div>
                <div className={styles.partnerInstruction} style={{paddingRight: 35}}>
                    <div className={styles.dot} />
                    Когда приглашённый зарегистрируется и оплатит сервис — ты получаешь до 50% от его оплаты на свой баланс.
                </div>

                {/*TODO URL partner*/}
                <WideButton
                    color="#transparent"
                    text={
                        <div className={styles.button}>
                            <img height="px" width="px" src="/assets/referral/partner-rules.svg" alt=" " />
                            Правила партнерской програмы
                        </div>
                    }
                    buttonStyle={{minHeight: 38, maxHeight: 38, color: "#FFFFFF66"}}
                    style={{marginTop: 5, borderRadius: 11, border: "1px solid #FFFFFF66"}}
                    onClick={() => navigate("https://google.com")}
                />
            </div>

            <WideButton
                color="#BEF81133"
                textColor="#BEF811"
                text={
                    <div className={styles.button}>
                        <MoveArrow height="24px" width="24px" color="#BEF811" />
                        Оплатить тариф с баланса
                    </div>
                }
                buttonStyle={{minHeight: 50, maxHeight: 50}}
                style={{borderRadius: 19}}
                onClick={handlePurchaseByBalance}
            />

            <WideButton
                color={"transparent"}
                text={
                    <div className={styles.button}>
                        <img height="13px" width="19px" src="/assets/money.svg" alt=" " />
                        Вывести баланс
                    </div>
                }
                buttonStyle={{minHeight: 48, maxHeight: 48}}
                style={{marginTop: 3, marginBottom: 17, borderRadius: 19, border: "1px solid #FFFFFF"}}
                onClick={() => Telegram.WebApp.openLink(SUPPORT_URL, {try_instant_view: true})}
            />

            <RefsList refs={refs!} />
            <Delimiter />

            <IncomeCalculator />

            <div className={styles.bonusesBlock}>
                <div className={styles.bonusesTitle}>
                    <span>
                        <span>Специальные бонусы для партнеров </span>
                        <span style={{color: "#BEF811"}}>{">"}</span>
                    </span>
                </div>

                <div className={styles.bonuses}>
                    <div className={styles.bonus}>
                        <div className={styles.bonusBackground} style={{top: 8, right: 8}}>
                            <img height="103px" width="116px" src="/assets/referral/beta-background.svg" alt=" " />
                        </div>

                        <div className={styles.bonusTitle}>
                            <span>
                                <span style={{color: "#BEF811"}}>//</span>
                                <span>Эксклюзивный ранний доступ</span>
                            </span>
                        </div>
                        <div className={styles.bonusDescription} style={{paddingRight: 150}}>
                            Получай новые инструменты и фишки первым, до официального релиза.
                        </div>
                    </div>
                    <div className={styles.bonus}>
                        <div className={styles.bonusBackground} style={{top: 0, right: 0}}>
                            <img height="119px" width="175px" src="/assets/referral/support-background.svg" alt=" " />
                        </div>

                        <div className={styles.bonusTitle}>
                            <span>
                                <span style={{color: "#BEF811"}}>//</span>
                                <span>Личный менеджер и поддержка</span>
                            </span>
                        </div>
                        <div className={styles.bonusDescription} style={{paddingRight: 140}}>
                            Быстрые ответы на любые вопросы, помощь с продвижением и интеграцией.
                        </div>
                    </div>
                    <div className={styles.bonus}>
                        <div className={styles.bonusBackground} style={{bottom: 0, right: 0}}>
                            <img height="87px" width="219px" src="/assets/referral/marketing-background.svg" alt=" " />
                        </div>

                        <div className={styles.bonusTitle}>
                            <span>
                                <span style={{color: "#BEF811"}}>//</span>
                                <span>Помощь команды маркетологов</span>
                            </span>
                        </div>
                        <div className={styles.bonusDescription} style={{paddingRight: 180}}>
                            Эксперты помогут с любыми вопросами по продвижению и увеличению дохода.
                        </div>
                    </div>
                </div>
            </div>

            <Delimiter />
            <BottomSection />
        </div>
    );
};

export default Referral;
