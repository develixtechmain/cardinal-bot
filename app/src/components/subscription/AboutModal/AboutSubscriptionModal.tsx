import styles from "./AboutSubscriptionModal.module.css";
import {FC} from "react";

import OverlayModal from "../../common/Alert/OverlayModal";
import WideButton from "../../common/Buttons/WideButton";
import Delimiter from "../../common/Delimiter/Delimiter";
import AboutSubscriptionTool from "./AboutSubscriptionTool";

import FullEagle from "../../../assets/subscription/full-eagle.svg";

interface AboutSubscriptionModalProps {
    isOpen: boolean;
    onClose: () => void;
    openAboutFinder: () => void;
    openAboutCatcher: () => void;
}

const AboutSubscriptionModal: FC<AboutSubscriptionModalProps> = ({isOpen, onClose, openAboutFinder, openAboutCatcher}) => {
    return (
        <OverlayModal isOpen={isOpen} onClose={onClose} centered={false}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.background}>
                        <img src="/assets/subscription/about/background.svg" alt=" " />
                    </div>
                    <div className={styles.header}>
                        <span style={{marginRight: 44}}>
                            <span>Один тариф - все функции за </span>
                            <span className={styles.purple}>4900руб</span>
                        </span>
                        <img height="28px" width="31px" src="/assets/finder/briefing/example-exit.svg" alt="CLOSE" onClick={onClose} />
                    </div>

                    <div className={styles.headerDescription}>Полный доступ к Cardinal: ИИ Лид‑файндер и Перехватчик лидов в одном пакете.</div>

                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", position: "relative", zIndex: 1}} />
                    <div className={styles.title}>Что входит в подписку?</div>

                    <AboutSubscriptionTool
                        title="Ai - лидфайндер"
                        first={true}
                        icon={<img height="59px" width="101px" src="/assets/subscription/about/finder.svg" alt=" " />}
                        description={[
                            {text: "Система находит релевантные заказы для фрилансеров и экспертов, "},
                            {text: "фильтрует их под твой профиль и показывает только те, что действительно нужны именно тебе.", bold: true}
                        ]}
                        about={[
                            [{text: "Индивидуальный брифинг — ИИ задаёт вопросы и формирует твой точный профиль."}],
                            [{text: "Умный поиск — анализирует биржи, чаты, форумы и закрытые площадки."}],
                            [{text: "Многоуровневая фильтрация — отсеивает спам и нерелевантные заказы.."}],
                            [{text: "Готовые отклики — вместе с заказом получаешь текст для быстрого ответа."}],
                            [{text: "Самообучение — чем больше ты пользуешься, тем точнее подбор."}]
                        ]}
                        summary={[
                            [
                                {text: "Персональный поток заказов", bold: true},
                                {
                                    text: "— система каждый день присылает только те заказы, которые идеально совпадают с твоим профилем (без 100+ «мусорных» заявок)."
                                }
                            ],
                            [
                                {text: "Фору перед конкурентами", bold: true},
                                {text: "— ты видишь новые заказы в первые минуты после публикации и можешь откликнуться раньше других."}
                            ],
                            [
                                {text: "Рост шансов на сделку — ", bold: true},
                                {text: "ты общаешься только с заказчиками, которые реально ищут именно твою услугу, без «холодных» и нерелевантных запросов."}
                            ]
                        ]}
                        openAboutToolModal={openAboutFinder}
                        close={onClose}
                    />

                    <AboutSubscriptionTool
                        title="Перехватчик лидов"
                        icon={<img height="59px" width="101px" src="/assets/subscription/about/contact-catcher.svg" alt=" " />}
                        description={[{text: "Система которая перехватывает контакты заявок с сайтов и звонков конкурентов"}]}
                        about={[
                            [{text: "Фиксация звонков", bold: true}, {text: "— система собирает номера людей, которые звонили в отделы продаж конкурентов."}],
                            [{text: "Перехват с сайтов", bold: true}, {text: "— получает контакты посетителей, заходивших на сайты конкурентов."}]
                        ]}
                        summary={[
                            [{text: "Готовые «горячие» контакты", bold: true}, {text: "— это люди, которые прямо сейчас ищут твой продукт или услугу."}],
                            [{text: "Самая низкая цена лида на рынке", bold: true}, {text: "— всего 25 ₽ за контакт (в 5–10 раз дешевле рекламы)."}],
                            [{text: "Экономия бюджета", bold: true}, {text: "— конкуренты тратят на рекламу, а ты получаешь их трафик."}]
                        ]}
                        openAboutToolModal={openAboutCatcher}
                        close={onClose}
                    />

                    <div className={styles.title} style={{fontSize: 25, marginTop: 15, marginBottom: 23}}>
                        {" "}
                        Тариф в деталях
                    </div>
                    <div className={styles.tariffDetail} style={{paddingRight: 90}}>
                        <div className={styles.dot} />
                        Принимаем карты РФ и зарубежные карты.
                    </div>
                    <div className={styles.tariffDetail} style={{paddingRight: 90}}>
                        <div className={styles.dot} />
                        Все платежи прозрачны, без скрытых комиссий.
                    </div>
                    <div className={styles.tariffDetail} style={{paddingRight: 55}}>
                        <div className={styles.dot} />У всех платных клиентов есть персональный менеджер (поможет с настройкой и стратегией).
                    </div>
                    <div className={styles.tariffDetail} style={{paddingRight: 40}}>
                        <div className={styles.dot} />
                        <div style={{display: "flex", flexDirection: "column", gap: 14}}>
                            <div>В одном тарифе можно вести до 5 параллельных задач/профессий</div>
                            <div className={styles.tariffDetailExample}>(например, одновременно искать заказы по дизайну, копирайтингу, таргету и т.д.).</div>
                        </div>
                    </div>

                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", position: "relative", zIndex: 1}} />
                    <div className={styles.legalBlock}>
                        <div className={styles.legalHeader}>
                            <span className={styles.purple}>//</span>
                            <span>Всё прозрачно и законно</span>
                        </div>

                        <div className={styles.legalDescription}>
                            <span>Cardinal — это не «серая схема» и не хакерские методы.</span>
                            <br />
                            <br />
                            <span>Мы работаем только с официально доступными данными и легальными технологиями.</span>
                            <br />
                            <br />
                            <span>Ваши заказы и контакты добываются так, чтобы бизнес всегда оставался в правовом поле.</span>
                        </div>
                    </div>
                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", position: "relative", zIndex: 1}} />

                    <WideButton
                        color="#7211F8"
                        text={
                            <div className={styles.purchaseButton}>
                                <FullEagle height="19px" width="33px" color="white" />
                                Офоромить подписку
                            </div>
                        }
                        buttonStyle={{minHeight: 47, maxHeight: 47, borderRadius: 12}}
                        onClick={onClose}
                    />
                </div>
            </div>
        </OverlayModal>
    );
};

export default AboutSubscriptionModal;
