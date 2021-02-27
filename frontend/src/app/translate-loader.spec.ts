import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { LanguageLoader } from "@app/translate-loader";
import { MockBuilder } from "ng-mocks";
import { of } from "rxjs";

describe("LanguageLoader", () => {
  let languageLoader: LanguageLoader;

  beforeEach(async () => {
    await MockBuilder(LanguageLoader, AppModule);
    (global as any).VERSION = "1";
    languageLoader = TestBed.inject(LanguageLoader);
  });

  describe("getTranslations", () => {
    it("should work under best conditions", done => {
      const classic = {
        a: "A",
        b: "B"
      };

      const ng = {
        c: "C",
        d: "D"
      };

      languageLoader.classicTranslations$ = () => of(classic);
      languageLoader.ngJsonTranslations$ = () => of(ng);
      languageLoader.ngTranslations$ = () => of(ng);

      languageLoader.getTranslation("en").subscribe(translation => {
        expect(translation).toEqual({ ...classic, ...ng });
        done();
      });
    });

    it("should fill missing values with key", done => {
      const classic = {
        a: "A",
        b: ""
      };

      const ng = {
        c: "C",
        d: ""
      };

      languageLoader.classicTranslations$ = () => of(classic);
      languageLoader.ngJsonTranslations$ = () => of(ng);
      languageLoader.ngTranslations$ = () => of(ng);

      languageLoader.getTranslation("en").subscribe(translation => {
        expect(translation).toEqual({
          a: "A",
          b: "b",
          c: "C",
          d: "d"
        });
        done();
      });
    });
  });
});
