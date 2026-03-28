import {User} from "./index";

export class UserImpl implements User {
    id: string;
    user_id: number;
    first_name?: string;
    last_name?: string;
    username?: string;
    avatar_url?: string;
    referrer_id?: string;
    balance: number;
    created_at: string;

    tg: WebAppUser;

    constructor(user: User) {
        this.id = user.id;
        this.user_id = user.user_id;
        this.first_name = user.first_name;
        this.last_name = user.last_name;
        this.username = user.username;
        this.avatar_url = user.avatar_url;
        this.referrer_id = user.referrer_id;
        this.balance = user.balance;
        this.created_at = user.created_at;
        this.tg = user.tg;
    }

    getUsername(): string {
        return this.username ?? "Unknown";
    }
}
