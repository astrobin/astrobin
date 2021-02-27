import { AppModule } from "@app/app.module";
import { UsernameComponent } from "@shared/components/misc/username/username.component";
import { UserProfileGenerator } from "@shared/generators/user-profile.generator";
import { UserGenerator } from "@shared/generators/user.generator";
import { MockBuilder, MockRender, ngMocks } from "ng-mocks";
import { UsernameService } from "./username.service";

describe("UsernameService", () => {
  let service: UsernameService;

  beforeEach(async () => {
    await MockBuilder(UsernameService, AppModule);
    MockRender(UsernameComponent);
    // Because it's a service of a component,
    // we need to get it in a special way.
    service = ngMocks.find(UsernameComponent).injector.get(UsernameService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("getDisplayName", () => {
    it("should be the username if the user profile doesn't have a real name", () => {
      const userProfile = UserProfileGenerator.userProfile();
      userProfile.realName = "";

      const user = UserGenerator.user();
      user.username = "foo";

      jest.spyOn(service.userStore, "getUserProfile").mockReturnValue(userProfile);

      expect(service.getDisplayName(user)).toEqual("foo");
    });

    it("should be the real name if the user profile has it", () => {
      const userProfile = UserProfileGenerator.userProfile();
      userProfile.realName = "Foo Bar";

      const user = UserGenerator.user();
      user.username = "foo";

      jest.spyOn(service.userStore, "getUserProfile").mockReturnValue(userProfile);

      expect(service.getDisplayName(user)).toEqual("Foo Bar");
    });
  });
});
