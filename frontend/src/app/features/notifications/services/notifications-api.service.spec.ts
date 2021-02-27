import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { MockBuilder } from "ng-mocks";
import { NotificationsApiService } from "./notifications-api.service";

describe("NotificationsApiService", () => {
  beforeEach(() => MockBuilder(NotificationsApiService, AppModule));

  it("should be created", () => {
    const service: NotificationsApiService = TestBed.inject(NotificationsApiService);
    expect(service).toBeTruthy();
  });
});
