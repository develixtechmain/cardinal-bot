import React, {useEffect, useRef, useState} from 'react';
import {Route, Switch} from 'wouter';
import {useStore} from "./store/store";
import Finder from './pages/finder/Finder';
import BriefingIntro from "./pages/finder/briefing/BriefingIntro";
import BriefingAlert from "./pages/finder/briefing/BriefingAlert";
import BriefingQuestion from "./pages/finder/briefing/BriefingQuestion";
import BriefingAdditional from "./pages/finder/briefing/BriefingAdditional";
import BriefingCompleted from "./pages/finder/briefing/BriefingCompleted";
import {fetchSubscription, fetchUser, patchUser} from "./api/base";
import {ProtectedRoute} from "./ProtectedRoute";
import BriefingVerify from "./pages/finder/briefing/BriefingVerify";
import ScrollToTop from "./ScrollToTop";
import {SubscriptionTrialUsed} from "./pages/SubscriptionTrialUsed";
import {Loading} from './components/common/Loading/Loading';
import Home from "./pages/Home";
import {ErrorBoundary} from "./components/common/Alert/ErrorBoundary";
import GlobalModals from "./components/common/Alert/GlobalModals";
import Referral from "./pages/Referral";
import FinderTasks from "./pages/finder/FinderTasks";
import Subscription from "./pages/Subscription";
import SubscriptionPurchase from "./pages/SubscriptionPurchase";

const App: React.FC = () => {
    const isUserLoading = useRef(false);
    const isSubscriptionLoading = useRef(false);

    const user = useStore(s => s.user);
    const setUser = useStore(s => s.setUser);
    const subscription = useStore(s => s.subscription);
    const setSubscription = useStore(s => s.setSubscription);

    const [loading, setLoading] = useState(true);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        if (user && subscription) setLoading(false);
    }, [user, subscription]);

    useEffect(() => {
        const tg = window.Telegram?.WebApp;
        if (!tg) {
            return;
        }

        if (!isReady) {
            tg.ready();
            setIsReady(true);
        }
    }, [isReady]);

    useEffect(() => {
        const tg = window.Telegram?.WebApp;
        if (!tg) return;

        if (!tg.initDataUnsafe?.user?.id) {
            console.error("Telegram user data is missing");
            return;
        }

        const tryFetchUser = async () => {
            const tgUser = tg.initDataUnsafe.user!;
            try {
                const fetchedUser = await fetchUser();
                setUser({
                    ...fetchedUser,
                    tg: tgUser,
                });
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user: ${error.message}. Retrying...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
                await tryFetchUser();
            }
        }

        const run = async () => {
            if (!user) {
                if (isUserLoading.current) return;
                isUserLoading.current = true;

                try {
                    await tryFetchUser();
                } catch (e: unknown) {
                    const error = e as Error;
                    console.error(`Failed to fetch user: ${error.message}`);
                } finally {
                    isUserLoading.current = false;
                }
            } else {
                if (user.avatar_url !== user.tg.photo_url ||
                    (user.username !== user.tg.username && !(user.tg.username == undefined && user.username === "Unknown"))) {
                    const updatedUser = await patchUser(user)
                    setUser({
                        ...updatedUser,
                        tg: tg.initDataUnsafe.user!,
                    });
                }
            }
        }

        void run();
    }, [user])

    useEffect(() => {
        const tryFetchSubscription = async () => {
            try {
                const fetchedSubscription = await fetchSubscription();
                setSubscription(fetchedSubscription);
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user subscription: ${error.message}. Retrying...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
                await tryFetchSubscription();
            }
        }

        const run = async () => {
            if (!subscription) {
                if (isSubscriptionLoading.current) return;
                isSubscriptionLoading.current = true;

                try {
                    await tryFetchSubscription();
                } catch (e: unknown) {
                    const error = e as Error;
                    console.error(`Failed to fetch user subscription: ${error.message}`);
                } finally {
                    isUserLoading.current = false;
                }
            }
        }
        void run();
    }, [subscription])

    if (loading) {
        return (
            <Loading/>
        );
    }

    return (
        <ErrorBoundary>
            <ScrollToTop/>
            <Switch>
                <Route path="/" component={() => <ProtectedRoute><Home/></ProtectedRoute>}/>
                <Route path="/subscription" component={() => <ProtectedRoute><Subscription/></ProtectedRoute>}/>
                <Route path="/subscription/purchase/:months">{() => <ProtectedRoute><SubscriptionPurchase/></ProtectedRoute>}</Route>
                <Route path="/subscription/trial-used" component={() => <ProtectedRoute><SubscriptionTrialUsed/></ProtectedRoute>}/>
                <Route path="/finder" component={() => <ProtectedRoute><Finder/></ProtectedRoute>}/>
                <Route path="/finder/tasks" component={() => <ProtectedRoute><FinderTasks/></ProtectedRoute>}/>
                <Route path="/finder/briefing" component={() => <ProtectedRoute><BriefingIntro/></ProtectedRoute>}/>
                <Route path="/finder/briefing/alert" component={() => <ProtectedRoute><BriefingAlert/></ProtectedRoute>}/>
                <Route path="/finder/briefing/questions" component={() => <ProtectedRoute><BriefingQuestion/></ProtectedRoute>}/>
                <Route path="/finder/briefing/questions/additional" component={() => <ProtectedRoute><BriefingAdditional/></ProtectedRoute>}/>
                <Route path="/finder/briefing/verify" component={() => <ProtectedRoute><BriefingVerify/></ProtectedRoute>}/>
                <Route path="/finder/briefing/completed" component={() => <ProtectedRoute><BriefingCompleted/></ProtectedRoute>}/>
                <Route path="/referral" component={() => <ProtectedRoute><Referral/></ProtectedRoute>}/>
                <Route>404 Not Found</Route>
            </Switch>
            <GlobalModals/>
        </ErrorBoundary>
    );
};

export default App;
