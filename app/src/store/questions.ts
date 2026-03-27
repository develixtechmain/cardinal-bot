import {Answer, Question, QuestionAnswer} from "../types/finder";
import specialists from "./specialists";

// prettier-ignore
export const baseQuestions: Question[] = [
    {
        question: "Чем вы занимаетесь?",
        description: "Укажите все ваши специальности - так подходящих заказов найдется больше.",
        examples: () => Array.from(specialists.keys()),
        hint: {
            description: "Опиши ключевые детали, которые помогут системе максимально точно собрать облако тегов:",
            good: [
                {
                    title: "Твоя роль и специализация",
                    description: "(UI/UX-дизайнер, копирайтер, маркетолог, Python-разработчик и т. д.)"
                },
                {
                    title: "Уровень и опыт",
                    description: "(junior/middle/senior или количество лет практики)"
                },
                {
                    title: "С кем обычно работаешь",
                    description: "(стартапы, e-commerce, B2B, локальные бизнесы)"
                },
                {
                    title: "Формат работы",
                    description: "(фриланс, аутстафф, постоянное сопровождение, проектная работа)"
                }
            ],
            bad: [
                {
                    title: "Одного слова:",
                    description: "«дизайнер», «разработчик», «маркетинг»"
                },
                {
                    title: "Фраз типа «делаю всё подряд».",
                    description: "Такие фразы не дают системе понять твою специализацию и навыки"
                },
                {
                    title: "Ответа без контекста",
                    description: "Непонятно для кого и в каком формате работаешь"
                }
            ],
            example: "Я UI/UX-дизайнер (senior), 4+ лет опыта. Работаю со стартапами и B2B/SaaS (финтех, e-commerce). Повышал конверсию на 15–20%, ускорял онбординг. Интересны фриланс-заказы и короткие проекты."
        }
    },
    {
        question: "Какие основные услуги ты предлагаешь?",
        description: "Укажи те услуги, за которые чаще всего берёшься.",
        examples: (selected) => selected.flatMap((key) => {
            const specialist = specialists.get(key);
            return specialist?.services ?? [];
        }),
        hint: {
            description: "Укажи основные услуги, за которые чаще всего берёшься. Это поможет системе точнее подбирать заказы.",
            good: [
                {
                    title: "Конкретные услуги",
                    description: "«дизайн лендингов», «настройка таргета», «копирайтинг статей»"
                },
                {
                    title: "Формат услуги",
                    description: "Разработка с нуля, сопровождение, оптимизация, редизайн"
                },
                {
                    title: "Ценность для клиента",
                    description: "Что даёт услуга: рост продаж, улучшение UX, экономия времени"
                }
            ],
            bad: [
                {
                    title: "Слишком общих формулировок:",
                    description: "«делаю сайты», «занимаюсь дизайном», «маркетинг»"
                },
                {
                    title: "Фраз типа «делаю всё подряд».",
                    description: "Не отражает твой основной профиль."
                },
                {
                    title: "Односложных ответов без деталей:",
                    description: "«дизайн», «тексты», «реклама»"
                }
            ],
            example: "Разрабатываю дизайн-макеты сайтов и лендингов, провожу редизайн интерфейсов, создаю дизайн-системы. Часто работаю с e-commerce и корпоративными сайтами. Основной фокус — повышение удобства и конверсии."
        }
    },
    {
        question: "С какими программами, платформами или сервисами ты обычно работаешь?",
        description: "Укажи инструменты, которые ты используешь в работе.",
        selection: true,
        examples: (selected) => selected.flatMap((key) => {
            const specialist = specialists.get(key);
            return specialist?.applications ?? [];
        }),
        hint: {
            description: "Укажи основные инструменты, с которыми работаешь. Это поможет системе точнее подбирать офферы.",
            good: [
                {
                    title: "Основные программы",
                    description: "Figma, Photoshop, Excel, Capcut, After Effects и т. д."
                },
                {
                    title: "Платформы",
                    description: "Tilda, n8n, make, Shopify, Я-директ,Авито "
                }
            ],
            bad: [
                {
                    title: "Слишком общее:",
                    description: "«Дизайнерские программы» / «Интернет-сервисы»."
                },
                {
                    title: "Устаревшие или нерелевантные инструменты:",
                    description: "Которые не показывают ценности для офферов."
                }
            ]
        }
    },
    {
        question: "Какие доп. услуги, связанные с твоим направлением, ты готов выполнить?",
        description: "Напиши, что можешь делать дополнительно: аудит, сопровождение, правки, консультации и т.д.",
        examples: (selected) => selected.flatMap((key) => {
            const specialist = specialists.get(key);
            return specialist?.additionalServices ?? [];
        }),
        hint: {
            description: "Укажи задачи, которые можешь взять помимо основной работы — это расширит твой профиль.",
            good: [
                {
                    title: "Форматы задач",
                    description: "Редизайн, правки, адаптация под мобильные, перенос в другую систему"
                },
                {
                    title: "Популярные задачи в нише",
                    description: "Которые часто пишут клиенты, но они не твой основной фокус."
                }
            ],
            bad: [
                {
                    title: "Фраз «любые доп. работы»",
                    description: "слишком размыто."
                },
                {
                    title: "Услуг, которые не относятся к твоей сфере",
                    description: "Например, дизайнер пишет «могу настроить рекламу»"
                }
            ],
            example: "Помимо интерфейсов могу брать редизайн лендингов, баннеры для соцсетей и презентации. Также делаю адаптацию макетов под мобильные."
        }
    },
    {
        question: "Какие типы проектов или задач тебе наиболее интересны и ближе всего по профилю?",
        description: "",
        examples: (selected) => selected.flatMap((key) => {
            const specialist = specialists.get(key);
            return specialist?.projectTypes ?? [];
        }),
        hint: {
            description: "Укажи конкретные форматы проектов и задач, с которыми хочешь работать. Это поможет системе точнее фильтровать офферы под твой профиль.",
            good: [
                {
                    title: "Типы проектов",
                    description: "лендинги, интернет-магазины, мобильные приложения, чат-боты и т. д."
                },
                {
                    title: "Ниши/сферы",
                    description: "Которые часто пишут клиенты, но они не твой основной фокус."
                }
            ],
            bad: [
                {
                    title: "Фраз «любые доп. работы»",
                    description: "слишком размыто."
                },
                {
                    title: "Услуг, которые не относятся к твоей сфере",
                    description: "Например, дизайнер пишет «могу настроить рекламу»"
                }
            ],
            example: "Интересны проекты по созданию лендингов и промо-сайтов, редизайн мобильных приложений и дашбордов для B2B. Ближе всего финтех и e-commerce."
        }
    }
];

export function totalAnswers(answers: Answer[], additionalQuestions: QuestionAnswer[]) {
    const totalAnswers: QuestionAnswer[] = [];
    for (let i = 0; i < baseQuestions.length; i++) {
        if (answers[i]) totalAnswers.push({question: baseQuestions[i].question, answer: answers[i].text, selections: answers[i].selections});
    }

    additionalQuestions.forEach((answer) => {
        if (answer) totalAnswers.push(answer);
    });
    return totalAnswers;
}
