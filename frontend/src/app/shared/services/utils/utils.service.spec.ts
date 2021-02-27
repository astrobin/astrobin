import { TestBed } from "@angular/core/testing";
import { MockBuilder } from "ng-mocks";

import { UtilsService } from "./utils.service";

describe("UtilsService", () => {
  let service: UtilsService;

  beforeEach(async () => {
    await MockBuilder(UtilsService);
    service = TestBed.inject(UtilsService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  describe("fileExtension", () => {
    it("should work", () => {
      expect(service.fileExtension("foo.txt")).toEqual("txt");
      expect(service.fileExtension("foo bar.txt")).toEqual("txt");
      expect(service.fileExtension("名称.txt")).toEqual("txt");
      expect(service.fileExtension("foo.bar.txt")).toEqual("txt");
      expect(service.fileExtension("foo")).toBeUndefined();
      expect(service.fileExtension("")).toBeUndefined();
      expect(service.fileExtension(null)).toBeUndefined();
      expect(service.fileExtension(undefined)).toBeUndefined();
    });
  });

  describe("isImage", () => {
    it("should be true for image extensions", () => {
      expect(service.isImage("foo.png")).toBe(true);
      expect(service.isImage("foo.jpg")).toBe(true);
      expect(service.isImage("foo.jpeg")).toBe(true);
      expect(service.isImage("foo.gif")).toBe(true);

      expect(service.isImage("foo.PNG")).toBe(true);
      expect(service.isImage("foo.JPG")).toBe(true);
      expect(service.isImage("foo.JPEG")).toBe(true);
      expect(service.isImage("foo.GIF")).toBe(true);
    });

    it("should be false for null/undefined extensions", () => {
      expect(service.isImage(undefined)).toBe(false);
      expect(service.isImage(null)).toBe(false);
    });

    it("should be false for TIFF/FITS extensions tho", () => {
      expect(service.isImage("foo.tif")).toBe(false);
      expect(service.isImage("foo.tiff")).toBe(false);
      expect(service.isImage("foo.fit")).toBe(false);
      expect(service.isImage("foo.fits")).toBe(false);
      expect(service.isImage("foo.fts")).toBe(false);

      expect(service.isImage("foo.TIF")).toBe(false);
      expect(service.isImage("foo.TIFF")).toBe(false);
      expect(service.isImage("foo.FIT")).toBe(false);
      expect(service.isImage("foo.FITS")).toBe(false);
      expect(service.isImage("foo.FTS")).toBe(false);
    });

    it("should be false for non-image extensions", () => {
      expect(service.isImage("foo.mov")).toBe(false);
      expect(service.isImage("foo.zip")).toBe(false);
      expect(service.isImage("foo.mp3")).toBe(false);
      expect(service.isImage("foo.mp4")).toBe(false);
      expect(service.isImage("foo.txt")).toBe(false);
    });
  });

  describe("arrayUniqueObjects", () => {
    it("should work with one property", () => {
      const a = { pk: 1 };
      const b = { pk: 2 };
      const c = { pk: 1 };

      expect(service.arrayUniqueObjects([a, b, c])).toEqual([a, b]);
    });

    it("should work with multiple property", () => {
      const a = { pk: 1, foo: "a" };
      const b = { pk: 1, foo: "b" };
      const c = { pk: 1, foo: "a" };

      expect(service.arrayUniqueObjects([a, b, c])).toEqual([a, b]);
    });
  });
});
