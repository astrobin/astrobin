import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsIotdSubmitterPipe } from "./is-iotd-submitter.pipe";

describe('IsIotdSubmitterPipe', () => {
  let pipe: IsIotdSubmitterPipe;

  beforeAll(() => {
    pipe = new IsIotdSubmitterPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for iotd submitters', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'iotd_submitters'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non iotd submitters', () => {
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
