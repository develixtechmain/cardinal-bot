import styles from "./Home.module.css";
import {FC, useState} from "react";

import {useLocation} from "wouter";

import ActionButtons from "../components/ActionButtons/ActionButtons";
import ClubSection from "../components/ClubSection/ClubSection";
import {ProfileSection} from "../components/ProfileSection/ProfileSection";
import SubscriptionAlert from "../components/SubscriptionAlert/SubscriptionAlert";
import ToolsSection from "../components/ToolsSection/ToolsSection";
import BottomSection from "../components/common/BottomSection/BottomSection";
import WideButton from "../components/common/Buttons/WideButton";
import Delimiter from "../components/common/Delimiter/Delimiter";
import Header from "../components/common/Header/Header";
import {Loading} from "../components/common/Loading/Loading";
import AboutContactCatcherModal from "../components/contact-catcher/AboutModal/AboutContactCatcherModal";
import AboutFinderModal from "../components/finder/AboutModal/AboutFinderModal";
import {useStore} from "../store/store";
import {actionButtons, tools} from "../utils/consts";

const Home: FC = () => {
    const [, navigate] = useLocation();
    const user = useStore((s) => s.user);
    const subscription = useStore((s) => s.subscription);
    const [isAboutFinderOpen, setIsAboutFinderOpen] = useState(false);
    const [isAboutCatcherOpen, setIsAboutContactCatcherOpen] = useState(false);

    if (!user) {
        return <Loading />;
    }

    return (
        <div className={styles.container}>
            <AboutFinderModal isOpen={isAboutFinderOpen} onClose={() => setIsAboutFinderOpen(false)} />
            <AboutContactCatcherModal isOpen={isAboutCatcherOpen} onClose={() => setIsAboutContactCatcherOpen(false)} />

            <Header />
            <ProfileSection user={user} subscription={subscription!} />
            {subscription!.isSubscriptionExpired() && (
                <div className={styles.subscriptionExpired}>
                    <SubscriptionAlert />
                    <WideButton
                        color={"#F81B1120"}
                        text={
                            <div className={styles.subscriptionExpiredButtonText}>
                                <img height="22px" width="21px" src="/assets/icons/key.svg" alt=" " />
                                Оформить подписку
                            </div>
                        }
                        buttonStyle={{minHeight: 60, maxHeight: 60}}
                        style={{border: "1px solid #F81B11", borderRadius: 19}}
                        onClick={() => navigate("/subscription")}
                    />
                </div>
            )}
            <Delimiter />
            <ToolsSection
                tools={Object.values(tools)}
                showModal={{finder: () => setIsAboutFinderOpen(true), "contact-catcher": () => setIsAboutContactCatcherOpen(true)}}
            />
            <ActionButtons
                buttons={actionButtons}
                isSubscriptionExpired={subscription!.isSubscriptionExpired()}
                isMoreThan3days={subscription!.daysLeft() > 3}
            />
            <ClubSection />
            <Delimiter />
            <BottomSection />
        </div>
    );
};

export default Home;
