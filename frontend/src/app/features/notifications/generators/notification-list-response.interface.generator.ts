import { NotificationInterfaceGenerator } from "@features/notifications/generators/notification.interface.generator";
import { NotificationListResponseInterface } from "@features/notifications/interfaces/notification-list-response.interface";

export class NotificationListResponseInterfaceGenerator {
  static notificationListResponse(): NotificationListResponseInterface {
    return {
      count: 1,
      previous: "",
      next: "",
      results: [NotificationInterfaceGenerator.notification()]
    };
  }
}
