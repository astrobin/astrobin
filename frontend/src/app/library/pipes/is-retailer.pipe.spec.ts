import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsRetailerPipe } from './is-retailer.pipe';

describe('IsRetailerPipe', () => {
  let pipe: IsRetailerPipe;

  beforeAll(() => {
    pipe = new IsRetailerPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for retailer', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'Retailers'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non retailer', () => {
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
