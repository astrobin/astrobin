import { UserModel } from "./user.model";

describe('UserModel', () => {
  it('isInGroup should work', () => {
    const user = new UserModel({
      groups: [
        {
          id: 1,
          name: "test-group"
        }
      ]
    });
    expect(user.isInGroup("test-group")).toBe(true);
  });

  it('isInGroup should work if no groups', () => {
    const user = new UserModel();
    expect(user.isInGroup("test-group")).toBe(false);
  });
});
