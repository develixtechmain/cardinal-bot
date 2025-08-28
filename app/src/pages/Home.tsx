import React from 'react';
import Header from '../components/common/Header/Header';
import SubscriptionAlert from '../components/SubscriptionAlert/SubscriptionAlert';
import ToolsSection from '../components/ToolsSection/ToolsSection';
import ActionButtons from '../components/ActionButtons/ActionButtons';
import ClubSection from '../components/ClubSection/ClubSection';
import BottomSection from '../components/common/BottomSection/BottomSection';
import styles from './Home.module.css';
import Delimiter from "../components/common/Delimiter/Delimiter";
import WideButton from "../components/common/Buttons/WideButton";
import {useStore} from "../store/store";
import {useLocation} from 'wouter';
import {ProfileSection} from "../components/ProfileSection/ProfileSection";
import {Loading} from "../components/common/Loading/Loading";
import {actionButtons, tools} from "../utils/consts";

const Home: React.FC = () => {
    const [, navigate] = useLocation();
    const user = useStore((s) => s.user);
    const subscription = useStore((s) => s.subscription);

    if (!user) {
        return <Loading/>
    }

    return (
        <div className={styles.container}>
            <Header/>
            <ProfileSection user={user} subscription={subscription!}/>
            {subscription!.isSubscriptionExpired() && (
                <div className={styles.subscriptionExpired}>
                    <SubscriptionAlert/>
                    <WideButton color={"#F81B1120"} text={
                        <div className={styles.subscriptionExpiredButtonText}>
                            <img height="22px" width="21px" src="/assets/icons/key.svg" alt=" "/>
                            Оформить подписку
                        </div>
                    } buttonStyle={{minHeight: 60, maxHeight: 60}} style={{
                        border: "1px solid #F81B11",
                        borderRadius: 19
                    }} onClick={() => navigate("/subscription")}/>
                </div>
            )}
            <Delimiter/>
            <ToolsSection tools={Object.values(tools)}/>
            <ActionButtons buttons={actionButtons} isSubscriptionExpired={subscription!.isSubscriptionExpired()}
                           isMoreThan3days={subscription!.daysLeft() > 3}/>
            <ClubSection/>
            <Delimiter/>
            <BottomSection/>
        </div>
    );
};

export default Home;
