import styles from "./Subscription.module.css";
import {CSSProperties, FC, useState} from "react";

import {useLocation} from "wouter";

import BottomSection from "../components/common/BottomSection/BottomSection";
import WideButton from "../components/common/Buttons/WideButton";
import Delimiter from "../components/common/Delimiter/Delimiter";
import Header from "../components/common/Header/Header";
import AboutContactCatcherModal from "../components/contact-catcher/AboutModal/AboutContactCatcherModal";
import AboutFinderModal from "../components/finder/AboutModal/AboutFinderModal";
import AboutSubscriptionModal from "../components/subscription/AboutModal/AboutSubscriptionModal";
import ManageSubscriptionModal from "../components/subscription/ManageModal/ManageSubscriptionModal";
import {useStore} from "../store/store";
import {TARIFF_PRICES_NORMALIZED, subscriptionBenefits} from "../utils/consts";

import Mark from "../assets/icons/mark.svg";
import AllInclusive from "../assets/subscription/all-inclusive.svg";
import Cash from "../assets/subscription/cash.svg";
import ContactCatcher from "../assets/subscription/contact-catcher.svg";
import FeaturesBackground from "../assets/subscription/features-background.svg";
import FullEagle from "../assets/subscription/full-eagle.svg";
import Money from "../assets/subscription/money.svg";
import Web from "../assets/subscription/web.svg";

const Subscription: FC = () => {
    const [, navigate] = useLocation();
    const [months, setMonths] = useState<number>(1);
    const [isAboutOpen, setIsAboutOpen] = useState(false);
    const [isManageOpen, setIsManageOpen] = useState(false);
    const [isAboutFinderOpen, setIsAboutFinderOpen] = useState(false);
    const [isAboutCatcherOpen, setIsAboutCatcherOpen] = useState(false);

    const subscription = useStore((state) => state.subscription);

    const subscriptionButton = (
        <WideButton
            color={months === 12 ? "#BEF811" : "#7211F8"}
            textColor={months === 12 ? "#000000" : "#FFFFFF"}
            text={
                <div className={styles.subscriptionButton}>
                    <Money height="21px" width="15px" color={months === 12 ? "#000000" : "#FFFFFF"} />
                    Оформить подписку
                </div>
            }
            buttonStyle={{minHeight: 47, maxHeight: 47}}
            style={{borderRadius: 19}}
            onClick={() => navigate(`/subscription/purchase/${months}`)}
        />
    );

    const contentColor = months === 1 ? "#7211F8" : months === 3 ? "#FFFFFF" : "#BEF811";
    const borderFromColor = months === 1 ? "#452A6B" : months === 3 ? "#452A6B" : "#452A6B";
    const borderToColor = months === 1 ? "#230D42" : months === 3 ? "#230D42" : "#BEF811";
    const featuresTitleColor = months === 1 ? "#7211F8" : months === 3 ? "#141414" : "#260E46";
    const featuresColor = months === 1 ? "#202020" : months === 3 ? "#7211F8" : "#BEF811";
    const featuresBackgroundColor = months === 1 ? "#7211F8" : months === 3 ? "#FFFFFF" : "#260E46";

    return (
        <div className={styles.container}>
            <Header height={82} top={0} backTo="" icon={<img height="82px" width="76px" src="/assets/subscription/header.svg" alt="CARDINAL PRO" />} />
            {(subscription?.subscription_ends_at || subscription?.trial_ends_at) && (
                <ManageSubscriptionModal isOpen={isManageOpen} onClose={() => setIsManageOpen(false)} subscription={subscription!} />
            )}
            <AboutSubscriptionModal
                isOpen={isAboutOpen}
                onClose={() => setIsAboutOpen(false)}
                openAboutFinder={() => {
                    setIsAboutOpen(false);
                    setIsAboutFinderOpen(true);
                }}
                openAboutCatcher={() => {
                    setIsAboutOpen(false);
                    setIsAboutCatcherOpen(true);
                }}
            />
            <AboutFinderModal
                isOpen={isAboutFinderOpen}
                onClose={() => {
                    setIsAboutFinderOpen(false);
                    setIsAboutOpen(true);
                }}
            />
            <AboutContactCatcherModal
                isOpen={isAboutCatcherOpen}
                onClose={() => {
                    setIsAboutCatcherOpen(false);
                    setIsAboutOpen(true);
                }}
            />

            <div className={styles.headerTitle}>
                <span>Один тариф - </span>
                <br />
                <span className={styles.purple}>все функции</span>
            </div>
            <div className={styles.headerSubtitle}>Полный доступ ко всем инструментам</div>

            <div className={styles.monthsSelector} style={{"--border-from": borderFromColor, "--border-to": borderToColor} as CSSProperties}>
                <div
                    className={`${styles.monthBlock} ${months === 1 ? styles.monthSelected : ""}`}
                    style={{"--month-from": "#7211F8", "--month-to": "#430A92", "--selected-left": "-9px", "--selected-right": "-8px"} as CSSProperties}
                    onClick={() => setMonths(1)}
                >
                    <span>
                        <span className={styles.purple}>//</span>
                        <span>Месяц</span>
                    </span>
                </div>
                <div
                    className={`${styles.monthBlock} ${months === 3 ? styles.monthSelected : ""}`}
                    style={{"--month-from": "#7211F8", "--month-to": "#430A92", "--selected-left": "-9px", "--selected-right": "-8px"} as CSSProperties}
                    onClick={() => setMonths(3)}
                >
                    <span>
                        <span className={styles.purple}>//</span>
                        <span>3 месяца</span>
                    </span>
                    <div className={styles.monthDiscount} style={{"--color": "#FFFFFF", "--background-color": "#7211F8"} as CSSProperties}>
                        -15%
                    </div>
                </div>
                <div
                    className={`${styles.monthBlock} ${months === 12 ? styles.monthSelected : ""}`}
                    style={{"--month-from": "#BEF811", "--month-to": "#6B8F00", "--selected-left": "-6px", "--selected-right": "-9px"} as CSSProperties}
                    onClick={() => setMonths(12)}
                >
                    <span>
                        <span className={styles.green}>//</span>
                        <span>Год</span>
                    </span>
                    <div className={styles.monthDiscount} style={{"--color": "black", "--background-color": "#BEF811"} as CSSProperties}>
                        -30%
                    </div>
                </div>
            </div>

            <div className={styles.featuresContainer}>
                <div className={styles.featuresTitle} style={{"--background-color": featuresTitleColor} as CSSProperties}>
                    ПОДПИСКА
                </div>
                {months === 3 ? (
                    <div className={styles.priceEconomy} style={{border: "1px solid #FFFFFF"}}>
                        <span>
                            <span>🔥 Экономия </span>
                            <span style={{fontWeight: 700}}>2 200 ₽</span>
                        </span>
                    </div>
                ) : (
                    months === 12 && (
                        <div className={styles.priceEconomy} style={{backgroundColor: "#260E46"}}>
                            <span>
                                <span>🔥 Экономия </span>
                                <span style={{color: "#BEF811"}}>16 800 ₽</span>
                            </span>
                        </div>
                    )
                )}

                <div className={styles.priceBlock} style={{"--background-color": featuresColor} as CSSProperties}>
                    <span style={{height: 30}}>
                        {months === 1 ? (
                            <span>
                                <span className={styles.purple}>{TARIFF_PRICES_NORMALIZED["1"]} </span>
                                <Cash height="21px" width="30px" className={styles.purple} />
                                <span style={{fontSize: 15}}>/мес</span>
                            </span>
                        ) : (
                            <div style={{marginTop: -5}}>
                                {months === 3 ? (
                                    <span>
                                        <span>{TARIFF_PRICES_NORMALIZED["3"]} </span>
                                        <Cash height="21px" width="30px" color="#FFFFFF" />
                                    </span>
                                ) : (
                                    <span>
                                        <span style={{color: "#260E46"}}>{TARIFF_PRICES_NORMALIZED["12"]} </span>
                                        <Cash height="21px" width="30px" color="#260E46" />
                                    </span>
                                )}
                            </div>
                        )}
                    </span>
                </div>
                <div className={styles.featuresSeparator} />
                <div className={styles.featuresBlock} style={{"--background-color": featuresColor} as CSSProperties}>
                    <div className={styles.featuresBackground}>
                        <FeaturesBackground color={featuresBackgroundColor} />
                    </div>
                    <div className={styles.features}>
                        <div className={styles.feature}>
                            <AllInclusive height="13px" width="13px" color={contentColor} style={{flexShrink: 0}} />
                            <div className={styles.featureDescription}>
                                <span className={styles.featureTitle}>Один тариф — всё включено</span>
                                <span>
                                    <span>Никаких пакетов и дополнительных оплат. Один тариф </span>
                                    <span style={{color: "#FFFFFF"}}>- доступ ко всем инструментам и функциям.</span>
                                </span>
                            </div>
                        </div>
                        <div className={styles.feature} style={{paddingRight: 40}}>
                            <Web height="13px" width="13px" color={contentColor} style={{flexShrink: 0}} />
                            <div className={styles.featureDescription}>
                                <span className={styles.featureTitle}>Прогнозируемый результат</span>
                                <span>
                                    <span>ИИ подстраивается под твои задачи и ежедневно </span>
                                    <span style={{color: "#FFFFFF"}}>находит релевантные заявки</span>
                                </span>
                            </div>
                        </div>
                        <div className={styles.feature}>
                            <ContactCatcher height="13px" width="16px" color={contentColor} style={{flexShrink: 0}} />
                            <div className={styles.featureDescription}>
                                <span className={styles.featureTitle}>Доступ к перехвату контактов</span>
                                <span>
                                    <span>Получай номера лидов конкурентов — по минимальной цене на рынке: </span>
                                    <span style={{color: "#FFFFFF"}}>всего 20₽ за контакт. </span>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <WideButton
                color={"transparent"}
                textColor={months === 12 ? "#BEF811" : "#7211F8"}
                text={
                    <div className={styles.aboutButton}>
                        <FullEagle height="19px" width="33px" color={months === 12 ? "#BEF811" : "#7211F8"} />
                        Подробнее о тарифе
                    </div>
                }
                buttonStyle={{minHeight: 45, maxHeight: 45}}
                style={{margin: "10px 0", borderRadius: 19, border: `1px solid ${months === 12 ? "#BEF811" : "#7211F8"}`}}
                onClick={() => setIsAboutOpen(true)}
            />

            {subscriptionButton}

            <div className={styles.benefitsTitle}>
                <span>
                    <span>Да, цена слишком дешевая за такой софт — ведь </span>
                    <span className={styles.purple} style={{textDecoration: "underline"}}>
                        за 49$ ты получаешь:
                    </span>
                </span>
            </div>

            {subscriptionBenefits.map((item, index) => (
                <div key={index} className={styles.benefitBlock}>
                    <div className={styles.benefitContainer}>
                        <div className={styles.benefitHeader}>
                            <img
                                height={`${item.title.icon.height}px`}
                                width={`${item.title.icon.width}px`}
                                src={`/assets/subscription/${item.title.text.id}-benefit-icon.svg`}
                                alt=" "
                            />
                            <span>
                                {item.title.text.textParts.map((item, index) => (
                                    <span key={index} style={{...item.styles, fontWeight: item.bold ? 700 : 400}}>
                                        {item.text}
                                    </span>
                                ))}
                            </span>
                        </div>
                        <div className={styles.benefitList}>
                            {item.text.map(({id, textParts, extraPadding}) => (
                                <div key={id} className={styles.benefit}>
                                    <Mark height="15px" width="15px" color="#7211F8" style={{flexShrink: 0}} />
                                    <div style={{paddingRight: extraPadding ?? 0} as CSSProperties}>
                                        {textParts.map(({bold, text}, index) => {
                                            const lines = text.split("\n");
                                            return (
                                                <span key={index}>
                                                    {lines.map((line, i) => (
                                                        <span key={i}>
                                                            <span style={{color: bold ? "#FFFFFF" : "#FFFFFF80"}}>{line}</span>
                                                            {i < lines.length - 1 && <br />}
                                                            {index <= textParts.length - 1 && <span> </span>}
                                                        </span>
                                                    ))}
                                                </span>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div />
                    </div>

                    <div>
                        <WideButton
                            color="#7211F833"
                            text={
                                <div className={styles.benefitButton}>
                                    <img
                                        height={`${item.button.height}px`}
                                        width={`${item.button.width}px`}
                                        src={`/assets/subscription/${item.title.text.id}-benefit-button.svg`}
                                        alt=" "
                                    />
                                    {item.button.label}
                                </div>
                            }
                            buttonStyle={{minHeight: 62, maxHeight: 62}}
                            style={{borderRadius: 19, border: "1px solid #7211F8"}}
                            onClick={() => navigate(`/subscription/purchase/${months}`)}
                        />
                        {index < subscriptionBenefits.length - 1 && <Delimiter />}
                    </div>
                </div>
            ))}

            <div className={styles.postscriptum}>
                <span>
                    <span style={{fontWeight: 700}}>P.S. </span>
                    <span>Это инвестиция в твой бизнес, а не просто подписка.</span>
                </span>
                <span>
                    <br />
                    <span style={{fontWeight: 700}}>4 900₽ в месяц </span>
                    <span>— меньше, чем один хороший заказ, а хороших заявок ты можешь получать до 50 в день</span>
                </span>
            </div>

            {subscriptionButton}

            {subscription!.isActive() && (
                <>
                    <Delimiter />
                    <WideButton
                        color="transparent"
                        text={
                            <div className={styles.manageSubscription}>
                                <img height="25px" width="25px" src="/assets/subscription/manage.svg" alt=" " />
                                Управление подпиской
                            </div>
                        }
                        buttonStyle={{minHeight: 62, maxHeight: 62}}
                        style={{borderRadius: 20, border: "1px solid #212121"}}
                        onClick={() => setIsManageOpen(true)}
                    />
                </>
            )}

            <Delimiter />
            <BottomSection />
        </div>
    );
};

export default Subscription;
