export interface Stats {
    guilds: number
    channels: number
    users: number
    commands: number
    uptime: Uptime
}

interface Uptime {
    total_seconds: string
    human_friendly: string
    days: number
    hours: number
    minutes: number
    seconds: number
}
