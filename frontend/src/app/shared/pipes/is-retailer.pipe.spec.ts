import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { UserGenerator } from "@shared/generators/user.generator";
import { UserService } from "@shared/services/user.service";
import { MockBuilder } from "ng-mocks";
import { IsRetailerPipe } from "./is-retailer.pipe";

describe("IsRetailerPipe", () => {
  let pipe: IsRetailerPipe;

  beforeAll(async () => {
    await MockBuilder(IsRetailerPipe, AppModule).provide(IsRetailerPipe);
    pipe = TestBed.inject(IsRetailerPipe);
  });

  it("create an instance", () => {
    expect(pipe).toBeTruthy();
  });

  it("pipe be true when user is in group", () => {
    jest.spyOn(pipe.userService, "isInGroup").mockReturnValue(true);
    expect(pipe.transform(UserGenerator.user())).toBe(true);
  });

  it("pipe be false when user is in not group", () => {
    jest.spyOn(pipe.userService, "isInGroup").mockReturnValue(false);
    expect(pipe.transform(UserGenerator.user())).toBe(false);
  });
});
