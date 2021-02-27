import { AppModule } from "@app/app.module";
import { NotificationInterfaceGenerator } from "@features/notifications/generators/notification.interface.generator";
import { NotificationsModule } from "@features/notifications/notifications.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { NotificationsPageComponent } from "./notifications-page.component";

describe("NotificationsPageComponent", () => {
  let component: NotificationsPageComponent;

  beforeEach(
    () => MockBuilder(NotificationsPageComponent, NotificationsModule).mock(AppModule) // parent module
  );

  beforeEach(() => {
    const fixture = MockRender(NotificationsPageComponent);
    component = fixture.point.componentInstance;
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });

  describe("toggleRead", () => {
    it("should call the right service method", () => {
      const notification = NotificationInterfaceGenerator.notification();
      notification.read = true;

      component.toggleRead(notification);

      expect(component.notificationsService.markAsUnread).toHaveBeenCalledWith(notification);

      notification.read = false;
      component.toggleRead(notification);

      expect(component.notificationsService.markAsRead).toHaveBeenCalledWith(notification);
    });
  });

  describe("markAllAsRead", () => {
    it("should call the service method", () => {
      component.markAllAsRead();

      expect(component.notificationsService.markAllAsRead).toHaveBeenCalled();
    });
  });

  describe("pageChange", () => {
    it("should get notification for that page from the service", () => {
      component.pageChange(2);

      expect(component.notificationsService.getAll).toHaveBeenCalledWith(2);
    });
  });
});
