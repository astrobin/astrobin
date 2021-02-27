import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { UserProfileGenerator } from "@shared/generators/user-profile.generator";
import { HasValidUserSubscriptionPipe } from "@shared/pipes/has-valid-user-subscription.pipe";
import { SubscriptionName } from "@shared/types/subscription-name.type";
import { MockBuilder } from "ng-mocks";
import { of } from "rxjs";

describe("HasValidUserSubscriptionPipe", () => {
  let pipe: HasValidUserSubscriptionPipe;

  beforeAll(async () => {
    await MockBuilder(HasValidUserSubscriptionPipe, AppModule).provide(HasValidUserSubscriptionPipe);
    pipe = TestBed.inject(HasValidUserSubscriptionPipe);
  });

  it("should create an instance", () => {
    expect(pipe).toBeTruthy();
  });

  it("pipe should work", done => {
    jest.spyOn(pipe.userSubscriptionService, "hasValidSubscription").mockReturnValue(of(true));
    pipe
      .transform(UserProfileGenerator.userProfile(), [SubscriptionName.ASTROBIN_PREMIUM_AUTORENEW])
      .subscribe(result => {
        expect(result).toBe(true);
        done();
      });
  });
});
