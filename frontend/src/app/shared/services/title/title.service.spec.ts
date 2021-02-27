import { TestBed } from "@angular/core/testing";
import { MockBuilder } from "ng-mocks";

import { TitleService } from "./title.service";

describe("TitleService", () => {
  let service: TitleService;

  beforeEach(async () => {
    await MockBuilder(TitleService);
    service = TestBed.inject(TitleService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("setTitle", () => {
    it("should append the site's name to the title", () => {
      jest.spyOn(service.titleService, "setTitle");

      service.setTitle("foo");

      expect(service.titleService.setTitle).toHaveBeenCalledWith("foo - AstroBin");
    });
  });
});
