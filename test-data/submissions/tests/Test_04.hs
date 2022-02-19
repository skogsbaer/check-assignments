{-# LANGUAGE QuasiQuotes #-}
{-# LANGUAGE OverloadedStrings #-}
module Test where

import qualified Main as C
import Test.HUnit

tutorMain :: IO ()
tutorMain =
  runTestTTAndExit $ TestCase $ assertEqual "tutorAssertion" 5 (C.foo 3)
