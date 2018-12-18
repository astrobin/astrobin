import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsContentModeratorPipe } from "./is-content-moderator.pipe";

describe('IsContentModeratorPipe', () => {
  let pipe: IsContentModeratorPipe;

  beforeAll(() => {
    pipe = new IsContentModeratorPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for content moderator', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'content_moderators'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non content moderator', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'Admins'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(false);
  });

  it('pipe should work if no groups', () => {
    const profile = new UserProfileModel();
    expect(pipe.transform(profile)).toBe(false);
  });
});
