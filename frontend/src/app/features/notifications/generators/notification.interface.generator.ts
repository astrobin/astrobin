import { NotificationInterface } from "@features/notifications/interfaces/notification.interface";

export class NotificationInterfaceGenerator {
  static notification(): NotificationInterface {
    return {
      id: 1,
      user: 1,
      subject: "Test notification subject",
      message: "Test notification body",
      level: 100,
      extraTags: "-",
      created: new Date("2010-01-01").toISOString(),
      modified: new Date("2010-01-02").toISOString(),
      read: false
    };
  }
}
