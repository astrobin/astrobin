import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { UserGenerator } from "@shared/generators/user.generator";
import { MockBuilder } from "ng-mocks";
import { IsIotdReviewerPipe } from "./is-iotd-reviewer.pipe";

describe("IsIotdReviewerPipe", () => {
  let pipe: IsIotdReviewerPipe;

  beforeAll(async () => {
    await MockBuilder(IsIotdReviewerPipe, AppModule).provide(IsIotdReviewerPipe);
    pipe = TestBed.inject(IsIotdReviewerPipe);
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
