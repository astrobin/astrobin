import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { MockBuilder } from "ng-mocks";
import { PopNotificationsService } from "./pop-notifications.service";

describe("PopNotificationsService", () => {
  let service: PopNotificationsService;

  beforeEach(async () => {
    await MockBuilder(PopNotificationsService, AppModule);
    service = TestBed.inject(PopNotificationsService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("success", () => {
    beforeEach(() => {
      spyOn(service.toastr, "success");
    });

    it("should defer to toastr module, with title", () => {
      service.success("message", "title");

      expect(service.toastr.success).toHaveBeenCalledWith("message", "title", undefined);
    });

    it("should defer to toastr module, without title", () => {
      service.success("message");

      expect(service.toastr.success).toHaveBeenCalledWith("message", "Success!", undefined);
    });
  });

  describe("info", () => {
    beforeEach(() => {
      spyOn(service.toastr, "info");
    });

    it("should defer to toastr module, with title", () => {
      service.info("message", "title");

      expect(service.toastr.info).toHaveBeenCalledWith("message", "title", undefined);
    });

    it("should defer to toastr module, without title", () => {
      service.info("message");

      expect(service.toastr.info).toHaveBeenCalledWith("message", "Info", undefined);
    });
  });

  describe("warning", () => {
    beforeEach(() => {
      spyOn(service.toastr, "warning");
    });

    it("should defer to toastr module, with title", () => {
      service.warning("message", "title");

      expect(service.toastr.warning).toHaveBeenCalledWith("message", "title", undefined);
    });

    it("should defer to toastr module, without title", () => {
      service.warning("message");

      expect(service.toastr.warning).toHaveBeenCalledWith("message", "Warning!", undefined);
    });
  });

  describe("error", () => {
    beforeEach(() => {
      spyOn(service.toastr, "error");
    });

    it("should defer to toastr module, with title", () => {
      service.error("message", "title");

      expect(service.toastr.error).toHaveBeenCalledWith("message", "title", undefined);
    });

    it("should defer to toastr module, without title", () => {
      service.error("message");

      expect(service.toastr.error).toHaveBeenCalledWith("message", "Error!", undefined);
    });
  });
});
