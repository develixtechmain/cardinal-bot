import {QuestionAnswer} from "./index";

export type Briefing = {id: string; user_id: string; questions: QuestionAnswer[]; status: "completed" | "uncompleted"; created_at: string};
