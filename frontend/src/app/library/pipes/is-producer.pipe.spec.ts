import { UserModel } from "../models/common/user.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { IsProducerPipe } from './is-producer.pipe';

describe('IsProducerPipe', () => {
  let pipe: IsProducerPipe;

  beforeAll(() => {
    pipe = new IsProducerPipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('pipe should work for producer', () => {
    const profile = new UserProfileModel({
      userObject: new UserModel({
        groups: [
          {
            id: 1,
            name: 'Producers'
          }
        ]
      })
    });
    expect(pipe.transform(profile)).toBe(true);
  });

  it('pipe should work for non producer', () => {
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
