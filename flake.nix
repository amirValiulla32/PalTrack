# SPDX-License-Identifier: AGPL-3.0-or-later

{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    loguru-intercepthandler.url = "github:amyipdev/loguru-intercepthandler";
    teestream.url = "github:amyipdev/teestream";
  };
  outputs = {self, nixpkgs, flake-utils, loguru-intercepthandler, teestream}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        pp = pkgs.python313Packages;
        #multiprocessing-logging = pp.buildPythonPackage rec {
        #  pname = "multiprocessing-logging";
        #  version = "0.3.4";
        #  src = pkgs.fetchFromGitHub {
        #    owner = "jruere";
        #    repo = pname;
        #    rev = "v${version}";
        #    sha256 = "sha256-rb+llnp0NJfQMwZ+GVnVjDlSJsRMsMyAReaR6DW9YUU=";
        #  };
        #};
        pythainlp = pp.buildPythonPackage rec {
          pname = "pythainlp";
          version = "5.0.5";
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-MVo4kpx0+HiWCIdHLQ0kKyX8RcQdMqpciaEVNy5mO9M=";
          };
          doCheck = false;
          propagatedBuildInputs = with pp; [
            pyyaml
            numpy
            pyicu
            #python-crfsuite
            requests
          ];
        };
        newspaper3k = pp.buildPythonPackage rec {
          pname = "newspaper3k";
          version = "0.2.8";
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-nxvT4ftI9ADHFav4dcx7Cme33c2H9Qya7rj8u72QBPs=";
          };
          doCheck = false;
          propagatedBuildInputs = with pp; [
            beautifulsoup4
            cssselect
            feedfinder2
            feedparser
            jieba
            lxml
            lxml-html-clean
            nltk
            pillow
            pythainlp
            python-dateutil
            pyyaml
            requests
            tinysegmenter
            tldextract
          ];
        };
        python-prctl = pp.buildPythonPackage rec {
          pname = "python-prctl";
          version = "1.8.1";
          buildInputs = with pkgs; [
            libcap
          ];
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-tMqaJafU8azk//0fOi5k71II/gX5KfPt1eJwgcp+Z84=";
          };
          doCheck = false;
        };
        basePkgs = with pkgs; [
          bash
          python313
        ] ++ (with pp; [
          feedparser
          orjson
          aiomysql
          loguru
          aiohttp
          aiodns
          newspaper3k
          python-prctl
          loguru-intercepthandler.packages.${system}.py13
          teestream.packages.${system}.default
          #multiprocessing-logging
        ]);
        feedsearch-crawler = pp.buildPythonPackage rec {
          pname = "feedsearch-crawler";
          version = "1.0.3";
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-e++RsznpAbT3/3/nOl/MEK6J2T8XSucZ4xWka5CZJsM=";
          };
          doCheck = false;
          propagatedBuildInputs = with pp; [
            aiohttp
            beautifulsoup4
            faust-cchardet
            aiodns
            uvloop
            w3lib
            feedparser
            brotlipy
            python-dateutil
            yarl
          ];
        };
        astroid = pp.buildPythonPackage rec {
          pname = "astroid";
          version = "3.3.8";
          nativeBuildInputs = with pp; [
            setuptools
          ];
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-qIx5lPkUpOqFcvrEeUWfSVXuzMh3vj8tlZozJzsM9As=";
          };
          doCheck = false;
          pyproject = true;
          propagatedBuildInputs = with pp; [
            typing-extensions
          ];
        };
        pylint = pp.buildPythonPackage rec {
          pname = "pylint";
          version = "3.3.3";
          nativeBuildInputs = with pp; [
            setuptools
          ];
          src = pp.fetchPypi {
            inherit pname version;
            sha256 = "sha256-B8YHUjsX5tFuKuDX71lgLjMsqnYq9kIDwktBwnE582o=";
          };
          pyproject = true;
          doCheck = false;
          propagatedBuildInputs = with pp; [
            dill
            platformdirs
            astroid
            pp.isort
            mccabe
            tomli
            tomlkit
            colorama
            typing-extensions
          ];
        };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = basePkgs ++ (with pkgs; [
            git
            git-crypt
            vim
            nano
            gnupg
            openssh
            lix
            feedsearch-crawler
            pylint
          ]);
        };
        packages.default = pkgs.stdenv.mkDerivation rec {
          name = "paltrack";
          src = ./.;
          installPhase = ''
            echo "Building has not been configured yet. Need to develop bootstrap.py first."
            exit 1
          '';
        };
      }
    );
}
