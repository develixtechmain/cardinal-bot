import styles from "./RefList.module.css";
import {FC, useEffect, useMemo, useRef, useState} from "react";

import {RefUser} from "../../types/referral";

interface RefsListPropsProps {
    refs: RefUser[];
}

export const RefsList: FC<RefsListPropsProps> = ({refs}) => {
    const blockRef = useRef<HTMLDivElement>(null);

    const [isOpen, setIsOpen] = useState(false);
    const [containerWidth, setContainerWidth] = useState(0);

    const noRef = <img height="40px" width="40px" src="/assets/referral/no-refs.svg" alt=" " />;

    useEffect(() => {
        if (!blockRef.current) return;

        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                setContainerWidth(entry.contentRect.width);
            }
        });

        observer.observe(blockRef.current);
        return () => observer.disconnect();
    }, []);

    const visibleRefs = useMemo(() => {
        const itemWidth = 50;
        const buttonWidth = isOpen ? 113 : 179;
        const availableWidth = containerWidth - buttonWidth;
        const maxItemsInLine = Math.max(0, Math.floor(availableWidth / itemWidth));

        if (refs.length === 0) {
            return Array(maxItemsInLine).fill(null);
        }

        if (isOpen) {
            if (refs.length < maxItemsInLine) {
                return [...refs, ...Array(maxItemsInLine - refs.length).fill(null)];
            }
            return refs;
        }

        return [...refs.slice(0, maxItemsInLine), ...Array(Math.max(0, maxItemsInLine - refs.length)).fill(null)];
    }, [refs, isOpen, containerWidth]);

    return (
        <div className={styles.container}>
            <div className={styles.title}>Твои приглашённые:</div>

            {refs.length === 0 ? (
                <div className={styles.noRefsBlock}>
                    {noRef}
                    <div className={styles.noRefsText}>
                        <span className={styles.noRefsTitle}>У тебя ещё нет приглашённых.</span>
                        <span className={styles.noRefsDescription}>Пригласи друзей, чтобы получать бонусы</span>
                    </div>
                </div>
            ) : (
                <div ref={blockRef} className={styles.refsBlock}>
                    {visibleRefs.map((ref, index) =>
                        ref ? (
                            <div
                                key={index}
                                className={styles.ref}
                                onClick={() =>
                                    ref.username
                                        ? Telegram.WebApp.openTelegramLink(`https://t.me/${ref.username}`)
                                        : console.log(`User ${ref.id} doesn't have a public username`)
                                }
                            >
                                <img height="40px" width="40px" src={ref.avatar_url} alt="" className={styles.refAvatar} />
                                <div
                                    className={styles.refStatus}
                                    style={{color: ref.billed ? "#BEF811" : "white", backgroundColor: ref.billed ? "#BEF8114D" : "#FFFFFF4D"}}
                                >
                                    {ref.billed ? "Оплатил" : "Ждет"}
                                </div>
                            </div>
                        ) : (
                            <div key={index} className={styles.ref}>
                                {noRef}
                                <div className={styles.refStatus} style={{backgroundColor: "#FFFFFF4D"}}>
                                    Пусто
                                </div>
                            </div>
                        )
                    )}
                    <div className={styles.refsButton} onClick={() => setIsOpen(!isOpen)}>
                        {isOpen ? "Скрыть  >" : "Посмотреть всех  >"}
                    </div>
                </div>
            )}
        </div>
    );
};
