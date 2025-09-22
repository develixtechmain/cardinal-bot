export type Question = {
    question: string;
    description: string;
    selection?: boolean;
    examples: (selected: string[]) => string[];
    hint: {description: string; good: {title: string; description: string}[]; bad: {title: string; description: string}[]; example: string};
};

export type Answer = {text: string; selections: Set<string>};

export type QuestionAnswer = {question: string; answer: string};

export type FinderTask = {id: string; title: string; tags: string[]; active: boolean; created_at: string};

export type FinderTaskStatistics = {avg: number; total: number; today: number};
