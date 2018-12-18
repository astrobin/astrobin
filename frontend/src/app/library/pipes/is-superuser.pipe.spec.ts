import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsSuperuserPipe } from './is-superuser.pipe';

describe('IsSuperuserPipe', () => {
  let pipe: IsSuperuserPipe;

  beforeAll(() => {
    pipe = new IsSuperuserPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for superuser', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        is_superuser: true
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non superuser', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        is_superuser: false
      })
    });
    expect(pipe.transform(profile)).toBe(false);
  });

  it('pipe should work if no groups', () => {
    const profile = new UserProfileModel();
    expect(pipe.transform(profile)).toBe(false);
  });
});
