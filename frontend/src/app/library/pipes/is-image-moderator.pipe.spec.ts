import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsImageModeratorPipe } from "./is-image-moderator.pipe";

describe('IsImageModeratorPipe', () => {
  let pipe: IsImageModeratorPipe;

  beforeAll(() => {
    pipe = new IsImageModeratorPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for image moderator', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'image_moderators'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non image moderator', () => {
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
