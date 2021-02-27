import { TestBed } from "@angular/core/testing";
import { MockBuilder } from "ng-mocks";

import { SessionService } from "./session.service";

describe("SessionService", () => {
  let service: SessionService;

  beforeEach(async () => {
    await MockBuilder(SessionService);
    service = TestBed.inject(SessionService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should put/get an object correctly", () => {
    service.put("foo", { foo: "foo" });

    expect(service.get("foo")).toEqual({ foo: "foo" });
  });

  it("should delete an object correctly", () => {
    service.put("one", 1);
    service.delete("one");

    expect(service.get("one")).toBeUndefined();
  });
});
