import {useEffect} from "react";

import {useLocation} from "wouter";

export default function ScrollToTop() {
    const [location] = useLocation();

    useEffect(() => {
        requestAnimationFrame(() => {
            setTimeout(() => {
                const topElement = document.body.firstElementChild?.firstElementChild;
                if (topElement) {
                    topElement.scrollIntoView({behavior: "auto"});
                } else {
                    window.scrollTo(0, 0);
                }
            }, 0);
        });
    }, [location]);

    useEffect(() => {
        const tg = window.Telegram?.WebApp;
        const intervalId = setInterval(() => {
            if (!tg) {
                return;
            }
            const telegramHeight = tg.viewportStableHeight || tg?.viewportHeight || window.innerHeight;
            document.documentElement.style.setProperty("--tg-vh", `${telegramHeight}px`);
        }, 1000);

        return () => clearInterval(intervalId);
    }, []);

    return null;
}
