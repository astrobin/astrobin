import { UserGenerator } from "@shared/generators/user.generator";
import { IsSuperUserPipe } from "./is-superuser.pipe";

describe("IsSuperuserPipe", () => {
  let pipe: IsSuperUserPipe;

  beforeAll(() => {
    pipe = new IsSuperUserPipe();
  });

  it("create an instance", () => {
    expect(pipe).toBeTruthy();
  });

  it("pipe be true when user is super user", () => {
    const user = UserGenerator.user();
    user.isSuperUser = true;
    expect(pipe.transform(user)).toBe(true);
  });

  it("pipe be false when user is not super user", () => {
    const user = UserGenerator.user();
    user.isSuperUser = false;
    expect(pipe.transform(user)).toBe(false);
  });
});
