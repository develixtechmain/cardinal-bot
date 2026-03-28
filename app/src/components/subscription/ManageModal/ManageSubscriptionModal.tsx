import styles from "./ManageSubscriptionModal.module.css";
import {FC, useEffect, useRef, useState} from "react";

import {deleteRecurrency, fetchRecurrency} from "../../../api/base";
import {Subscription} from "../../../types";
import {formatToDayMonth} from "../../../utils/date";
import OverlayModal from "../../common/Alert/OverlayModal";

import Eagle from "../../../assets/icons/eagle.svg";

interface ManageSubscriptionModalProps {
    isOpen: boolean;
    onClose: () => void;
    subscription: Subscription;
}

const ManageSubscriptionModal: FC<ManageSubscriptionModalProps> = ({isOpen, onClose, subscription}) => {
    const endsAt = subscription.subscription_ends_at || subscription.trial_ends_at;

    const recurrencyLoading = useRef<boolean>(false);
    const recurrencyRemoving = useRef<boolean>(false);
    const [recurrency, setRecurrency] = useState(false);

    useEffect(() => {
        const run = async () => {
            if (recurrencyLoading.current) return;
            recurrencyLoading.current = true;

            setRecurrency(await fetchRecurrency());
        };
        void run();
    }, []);

    const handleRemoveRecurrency = async () => {
        if (recurrencyRemoving.current) return;
        recurrencyRemoving.current = true;

        try {
            await deleteRecurrency();
            setRecurrency(false);
        } finally {
            recurrencyRemoving.current = false;
        }
    };

    return (
        <OverlayModal isOpen={isOpen} onClose={onClose}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container}>
                    <img height="22px" width="24px" className={styles.close} src="/assets/icons/exit.svg" alt=" " />
                    <span className={styles.title}>
                        <span>Ваша подписка </span>
                        <span className={styles.purple}>{">"}</span>
                    </span>

                    <div className={styles.subscription}>
                        <div className={styles.subscriptionHeader}>
                            <div className={styles.subscriptionTitle}>
                                <div className={styles.dot} />
                                Cardinal Pro
                            </div>
                            <Eagle height="20px" width="20px" color="#7211F8" />
                        </div>
                        <span className={styles.subscriptionEnds}>
                            <span className={styles.purple}>//</span>
                            <span>Тариф активен до </span>
                            <span className={styles.bold}>{formatToDayMonth(endsAt!)}</span>
                        </span>
                    </div>

                    <span className={styles.title}>
                        <span>Автосписание </span>
                        <span className={styles.purple}>{"> "}</span>
                    </span>

                    <div className={styles.recurrencyBlock}>
                        <div className={styles.recurrencyStatus}>{recurrency ? "Подключено" : "Отключено"}</div>
                        <div className={`${styles.recurrencyButton} ${recurrency && styles.active}`} onClick={recurrency ? handleRemoveRecurrency : undefined}>
                            {recurrency ? "ВКЛ" : "ВЫКЛ"}
                        </div>
                    </div>
                </div>
            </div>
        </OverlayModal>
    );
};

export default ManageSubscriptionModal;
