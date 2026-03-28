import {Benefit} from "../types";
import {ActionButton, Tool} from "../types/home";

const rawBackendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL;
const rawAiCoreBaseUrl = import.meta.env.VITE_AI_CORE_BASE_URL;

export type ToolID = "finder" | "contact-catcher";
export type Service = "backend" | "ai_core";
export type Bank = "ru" | "external";

export const BACKEND_BASE_URL = rawBackendBaseUrl.replace(/\/+$/, "");
export const AI_CORE_BASE_URL = rawAiCoreBaseUrl.replace(/\/+$/, "");

export const SERVICE_LOCATOR = {backend: BACKEND_BASE_URL, ai_core: AI_CORE_BASE_URL};

export const TARIFF_PRICES = {1: 4900, 3: 12500, 12: 42000};

export const TARIFF_PRICES_NORMALIZED = Object.fromEntries(
    Object.entries(TARIFF_PRICES).map(([k, v]) => [k, v >= 10000 ? v.toLocaleString("ru-RU") : String(v)])
);

export const tools: {[key in ToolID]: Tool} = {
    finder: {
        id: "finder",
        title: "ИИ лид",
        subtitle: "файндер",
        description: "Получайте самые релевантные заказы на ваши услуги",
        selectorParts: ["ИИ лид", "файндер"],
        url: "/finder",
        external: false
    },
    "contact-catcher": {
        id: "contact-catcher",
        title: "Перехват",
        subtitle: "контактов",
        description: "Получайте контакты лидов ваших конкурентов которые звонили им либо посещали их сайты",
        selectorParts: ["Перехват контактов"],
        url: "https://david-nonstop.ru/perexvat",
        external: true
    }
};

export const actionButtons: ActionButton[] = [
    {id: "tariff", buttonLabel: "Тариф и оплата", color: "#F8E811", colorOpacity: 0.2, expiredColor: "#F81B11", longColor: "#7211F8", url: "/subscription"},
    {id: "ref", buttonLabel: "Реферальная система", color: "#141414", borderColor: "#BEF811", buttonColor: "#202020", contentColor: "#F2F2F2", url: "/referral"}
];

export const subscriptionBenefits: Benefit[] = [
    {
        title: {
            icon: {height: 26, width: 32},
            text: {
                id: "finder",
                textParts: [
                    {text: "Собственный "},
                    {text: "ИИ Лид", bold: true},
                    {text: "//", bold: true, styles: {color: "#7211F8"}},
                    {text: "файндер", bold: true}
                ]
            }
        },
        text: [
            {id: "machine", extraPadding: 110, textParts: [{text: "Сам парсит чаты,форумы и"}, {text: "закрытые каналы 24/7", bold: true}]},
            {
                id: "learning",
                textParts: [
                    {text: "ИИ постоянно самообучается", bold: true},
                    {text: "на твоих откликах, и с каждым днём подбирает для тебя всё более точные и релевантные заявки."}
                ]
            },
            {
                id: "filtering",
                textParts: [{text: "5 этапов ИИ фильтрации:", bold: true}, {text: "передаются только самые перспективные и реально интересные заявки."}]
            },
            {id: "stream", extraPadding: 110, textParts: [{text: "Гарантированный"}, {text: "поток \n квал-лидов", bold: true}, {text: "24/7"}]}
        ],
        button: {height: 15, width: 14, label: "Получить доступ к системе"}
    },
    {
        title: {
            icon: {height: 26, width: 26},
            text: {
                id: "contact-catcher",
                textParts: [
                    {text: "Перехватчика "},
                    {text: "лидов", bold: true},
                    {text: "//", bold: true, styles: {color: "#7211F8"}},
                    {text: "конкурентов", bold: true}
                ]
            }
        },
        text: [
            {
                id: "contacts",
                extraPadding: 20,
                textParts: [{text: "Получает"}, {text: "номера клиентов, звонивших твоим конкурентам", bold: true}, {text: "или заходивших на их сайты"}]
            },
            {id: "price", textParts: [{text: "Возможность получать лиды дешевле всех —"}, {text: "всего 25₽ за перехваченный лид конкурента", bold: true}]},
            {
                id: "fresh",
                extraPadding: 10,
                textParts: [{text: "Все контакты — свежие, появляются"}, {text: "уже через час после обращения к конкуренту.", bold: true}]
            },
            {id: "support", textParts: [{text: "Круглосуточная поддержка —", bold: true}, {text: "подскажем и поможем с любым вопросом."}]}
        ],
        button: {height: 22, width: 15, label: "Оформить подписку раньше конкурентов"}
    }
];

export const SUPPORT_URL = "https://t.me/cardinal_support_bot";
export const DOCS_URL = "https://cardinalx.gitbook.io/";
