import styles from "./ProfileSection.module.css";
import {FC, useRef} from "react";

import {useLocation} from "wouter";

import {startSubscriptionTrial} from "../../api/base";
import {useStore} from "../../store/store";
import {Subscription, User} from "../../types";
import {getDaysLeftEnding} from "../../utils/text";

import Eagle from "../../assets/icons/eagle.svg";
import MoveArrowIcon from "../../assets/icons/move-arrow.svg";

interface ProfileSectionProps {
    user: User;
    subscription: Subscription;
}

export const ProfileSection: FC<ProfileSectionProps> = ({user, subscription}) => {
    const [, navigate] = useLocation();
    const isSubscriptionExpired = subscription.isSubscriptionExpired();
    const daysLeft = subscription.daysLeft();
    const isMoreThan3days = daysLeft > 3;
    const setSubscription = useStore((s) => s.setSubscription);

    const trialRequested = useRef(false);
    const textColor = isSubscriptionExpired || isMoreThan3days ? "white" : "black";
    const contentColor = isSubscriptionExpired ? "#F81B11" : isMoreThan3days ? "#7211F8" : "#F8E811";
    const backgroundColor = isSubscriptionExpired ? "#F81B114D" : isMoreThan3days ? "#7211F84D" : "#F8E8114D";

    async function handleUseTrial() {
        if (trialRequested.current) return;
        trialRequested.current = true;

        const sub = await startSubscriptionTrial(subscription?.id!);
        setSubscription(sub);
        navigate("/subscription/trial-used");
    }

    return (
        <>
            <div className={styles.container} style={{"--bottom-padding": `${isSubscriptionExpired ? 40 : 12}px`} as React.CSSProperties}>
                <div className={styles.header}>
                    <img height="30px" width="30px" src={user.avatar_url} alt=" " />
                    <div className={styles.usernameContainer}>
                        <span className={styles.username}>{`@${user.username}`}</span>
                    </div>
                    <div style={{flex: 1}} />
                    <div className={styles.eagleContainer}>
                        <Eagle height="16px" width="16px" />
                    </div>
                </div>
                {isSubscriptionExpired && subscription.isTrialUsed() ? (
                    <div className={styles.expiredSubscription} style={{"--background-color": backgroundColor} as React.CSSProperties}>
                        <div className={styles.daysLeftHeader}>
                            <span className={styles.daysLeftHeaderText}>//Тариф истекает</span>
                            <Eagle height="16px" width="16px" color={contentColor} />
                        </div>
                        <div className={styles.daysLeftText} style={{"--color": contentColor} as React.CSSProperties}>
                            <span>{daysLeft}</span>
                            <div className={styles.daysLeftSubtext}>/дней</div>
                        </div>
                        <div
                            className={styles.subscriptionButton}
                            onClick={() => navigate("/subscription")}
                            style={{"--background-color": contentColor, "--color": textColor} as React.CSSProperties}
                        >
                            <span>Тариф и оплата</span>
                        </div>
                    </div>
                ) : (
                    <div className={styles.goodSubscription}>
                        <div
                            className={styles.goodTariffSection}
                            style={{"--border-color": contentColor, "--background-color": backgroundColor} as React.CSSProperties}
                        >
                            <div className={styles.daysLeftHeader}>
                                <span className={styles.daysLeftHeaderText}>//Тариф истекает</span>
                                <Eagle height="16px" width="16px" color={contentColor} />
                            </div>
                            <div className={styles.daysLeftText} style={{"--color": contentColor} as React.CSSProperties}>
                                <span>{daysLeft}</span>
                                <div className={styles.daysLeftSubtext}>/{getDaysLeftEnding(daysLeft)}</div>
                            </div>
                            <div
                                className={styles.subscriptionButton}
                                onClick={() => navigate("/subscription")}
                                style={{"--background-color": contentColor, "--color": textColor} as React.CSSProperties}
                            >
                                <span>Тариф и оплата</span>
                            </div>
                        </div>
                        {!subscription.isTrialUsed() && (
                            <div className={styles.trialContainer} onClick={handleUseTrial}>
                                <div className={styles.trialInfo} style={{"--background-color": "#BEF81133"} as React.CSSProperties}>
                                    <img height="13px" width="13px" src="/assets/icons/trial-lock.svg" alt=" " />
                                    <span>Пробный доступ</span>
                                </div>
                                <div className={styles.trialButton}>
                                    <MoveArrowIcon />
                                    <span>Активировать</span>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
            {isSubscriptionExpired && (
                <img style={{position: "relative", top: -25, left: "50%", transform: "translateX(-50%)"}} src="/assets/icons/lock.svg" alt=" " />
            )}
        </>
    );
};
